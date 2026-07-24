from io import BytesIO

from fastapi.testclient import TestClient
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage, generate_uid

from app.main import app
from app.storage.file_storage import LocalFileStorage, get_file_storage


def dicom_bytes() -> bytes:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = generate_uid()
    dataset.SeriesInstanceUID = generate_uid()
    dataset.Modality = "MR"
    dataset.StudyDate = "20260722"
    dataset.Rows = 1
    dataset.Columns = 1
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.PixelData = b"\0\0"
    output = BytesIO()
    dataset.save_as(output, enforce_file_format=True)
    return output.getvalue()


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def patient_id(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/patients",
        headers=headers,
        json={
            "first_name": "Imane",
            "last_name": "Rami",
            "birth_date": "1980-01-02",
            "sex": "female",
        },
    )
    return response.json()["id"]


def test_upload_list_get_and_delete_dicom(client: TestClient, tmp_path) -> None:
    storage = LocalFileStorage(root=tmp_path)
    app.dependency_overrides[get_file_storage] = lambda: storage
    headers = auth_headers(client)
    patient = patient_id(client, headers)

    uploaded = client.post(
        f"/patients/{patient}/imaging-studies",
        headers=headers,
        files={"file": ("brain.dcm", dicom_bytes(), "application/dicom")},
    )
    assert uploaded.status_code == 201
    study = uploaded.json()
    assert study["modality"] == "MR"
    assert study["original_file_uri"].endswith("/original.dcm")
    assert study["metadata_json"]["StudyInstanceUID"]
    assert len(study["sha256"]) == 64

    listed = client.get(f"/patients/{patient}/imaging-studies", headers=headers)
    assert [item["id"] for item in listed.json()] == [study["id"]]
    assert client.get(f"/imaging-studies/{study['id']}", headers=headers).status_code == 200

    deleted = client.delete(f"/imaging-studies/{study['id']}", headers=headers)
    assert deleted.status_code == 204
    assert not list(tmp_path.rglob("*.dcm"))
    app.dependency_overrides.pop(get_file_storage, None)


def test_reject_non_dicom_file(client: TestClient, tmp_path) -> None:
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(root=tmp_path)
    headers = auth_headers(client)
    patient = patient_id(client, headers)
    response = client.post(
        f"/patients/{patient}/imaging-studies",
        headers=headers,
        files={"file": ("fake.dcm", b"not a dicom", "application/dicom")},
    )
    assert response.status_code == 415
    assert not list(tmp_path.rglob("*.dcm"))
    app.dependency_overrides.pop(get_file_storage, None)


def test_reject_dicom_without_image_pixels(client: TestClient, tmp_path) -> None:
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(root=tmp_path)
    headers = auth_headers(client)
    patient = patient_id(client, headers)
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    output = BytesIO()
    dataset.save_as(output, enforce_file_format=True)
    response = client.post(
        f"/patients/{patient}/imaging-studies",
        headers=headers,
        files={"file": ("metadata-only.dcm", output.getvalue(), "application/dicom")},
    )
    assert response.status_code == 415
    app.dependency_overrides.pop(get_file_storage, None)


def test_reject_nifti_even_if_content_is_dicom(client: TestClient, tmp_path) -> None:
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(root=tmp_path)
    headers = auth_headers(client)
    patient = patient_id(client, headers)
    response = client.post(
        f"/patients/{patient}/imaging-studies",
        headers=headers,
        files={"file": ("brain.nii.gz", dicom_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 415
    app.dependency_overrides.pop(get_file_storage, None)


def test_imaging_routes_require_authentication(client: TestClient) -> None:
    response = client.get(
        "/patients/00000000-0000-0000-0000-000000000000/imaging-studies"
    )
    assert response.status_code == 401
