"""Tests for /api/logos endpoints.

Includes comprehensive SSRF validation tests addressing review feedback:
Codex flagged insufficient test coverage for the logo proxy's security surface.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException


class TestLogoProxy:
    """Tests for the HTTP endpoint."""

    def test_missing_domain(self, authed_client):
        resp = authed_client.get("/api/logos/proxy")
        assert resp.status_code == 422

    def test_no_token_configured(self, authed_client):
        """When LOGO_DEV_TOKEN is empty, should return 503."""
        with patch("app.api.logos.settings") as mock_settings:
            mock_settings.logo_dev_token = ""
            resp = authed_client.get("/api/logos/proxy?domain=stripe.com")
            assert resp.status_code == 503

    def test_domain_too_short(self, authed_client):
        resp = authed_client.get("/api/logos/proxy?domain=ab")
        assert resp.status_code == 422

    def test_ip_address_rejected_via_endpoint(self, authed_client):
        """IP addresses should be rejected at the domain validation level."""
        with patch("app.api.logos.settings") as mock_settings:
            mock_settings.logo_dev_token = "test-token"
            resp = authed_client.get("/api/logos/proxy?domain=192.168.1.1")
            assert resp.status_code == 400

    def test_localhost_rejected_via_endpoint(self, authed_client):
        """Localhost should be rejected."""
        with patch("app.api.logos.settings") as mock_settings:
            mock_settings.logo_dev_token = "test-token"
            resp = authed_client.get("/api/logos/proxy?domain=localhost")
            assert resp.status_code == 400


class TestLogoDomainValidation:
    """Unit tests for _validate_domain function.

    Tests SSRF protections directly without going through the HTTP stack.
    Addresses Codex review: more logo proxy test cases needed.
    """

    def test_valid_domain(self):
        from app.api.logos import _validate_domain

        assert _validate_domain("stripe.com") == "stripe.com"

    def test_valid_subdomain(self):
        from app.api.logos import _validate_domain

        assert _validate_domain("img.logo.dev") == "img.logo.dev"

    def test_valid_long_domain(self):
        from app.api.logos import _validate_domain

        assert _validate_domain("quickbooks.intuit.com") == "quickbooks.intuit.com"

    def test_case_normalization(self):
        from app.api.logos import _validate_domain

        assert _validate_domain("Stripe.COM") == "stripe.com"

    def test_ip_v4_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("192.168.1.1")
        assert exc_info.value.status_code == 400
        assert "IP addresses not allowed" in exc_info.value.detail

    def test_ip_v4_localhost_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("127.0.0.1")
        assert exc_info.value.status_code == 400

    def test_ipv6_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("[::1]")
        assert exc_info.value.status_code == 400
        assert "IPv6" in exc_info.value.detail

    def test_ipv6_full_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("::ffff:10.0.0.1")
        assert exc_info.value.status_code == 400

    def test_localhost_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("localhost")
        assert exc_info.value.status_code == 400

    def test_dot_local_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("server.local")
        assert exc_info.value.status_code == 400

    def test_dot_internal_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("app.internal")
        assert exc_info.value.status_code == 400

    def test_dot_example_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("test.example")
        assert exc_info.value.status_code == 400

    def test_invalid_fqdn_leading_hyphen(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("-invalid.com")
        assert exc_info.value.status_code == 400

    def test_single_label_no_tld(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("noextension")
        assert exc_info.value.status_code == 400

    def test_whitespace_stripped(self):
        from app.api.logos import _validate_domain

        assert _validate_domain("  stripe.com  ") == "stripe.com"

    def test_dot_onion_rejected(self):
        from app.api.logos import _validate_domain

        with pytest.raises(HTTPException) as exc_info:
            _validate_domain("hidden.onion")
        assert exc_info.value.status_code == 400
