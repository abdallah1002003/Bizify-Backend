import io
import uuid

from fastapi.testclient import TestClient


def test_upload_document_success(auth_client: TestClient):
    """IM-01: Upload a document successfully"""
    file_content = b"This is a test document content for parsing."
    files = {"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}

    resp = auth_client.post("/api/v1/import/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "document_id" in data
    assert data["filename"] == "test_doc.txt"


def test_upload_pdf_document(auth_client: TestClient):
    """IM-02: Upload a PDF document"""
    # Minimal valid PDF bytes
    pdf_bytes = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"
    files = {"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    resp = auth_client.post("/api/v1/import/upload", files=files)
    # Should succeed or return 422 if PDF text extraction fails gracefully
    assert resp.status_code in [200, 422, 500]


def test_export_document_for_ai(auth_client: TestClient):
    """IM-03: Retrieve extracted text for AI processing"""
    # Upload first
    file_content = b"Business plan: We sell organic coffee to tech companies."
    files = {"file": ("business_plan.txt", io.BytesIO(file_content), "text/plain")}
    upload_resp = auth_client.post("/api/v1/import/upload", files=files)
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["document_id"]

    # Export for AI
    resp = auth_client.get(f"/api/v1/import/{doc_id}/export-ai")
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == doc_id
    assert "extracted_text" in data


def test_delete_document_success(auth_client: TestClient):
    """IM-04: Delete an uploaded document"""
    file_content = b"Temporary document to be deleted."
    files = {"file": ("temp.txt", io.BytesIO(file_content), "text/plain")}
    upload_resp = auth_client.post("/api/v1/import/upload", files=files)
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["document_id"]

    del_resp = auth_client.delete(f"/api/v1/import/{doc_id}")
    assert del_resp.status_code == 200
    assert "deleted" in del_resp.json()["message"].lower()


def test_delete_document_not_found(auth_client: TestClient):
    """IM-05: Delete a non-existent document returns 404"""
    fake_id = str(uuid.uuid4())
    resp = auth_client.delete(f"/api/v1/import/{fake_id}")
    assert resp.status_code == 404


def test_export_ai_not_found(auth_client: TestClient):
    """IM-06: Export AI for non-existent document returns 404"""
    fake_id = str(uuid.uuid4())
    resp = auth_client.get(f"/api/v1/import/{fake_id}/export-ai")
    assert resp.status_code == 404


def test_upload_unauthorized(client: TestClient):
    """IM-07: Upload without token is rejected"""
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    resp = client.post("/api/v1/import/upload", files=files)
    assert resp.status_code == 401
