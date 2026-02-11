"""Simple test script to verify SSH Tunnel Manager can run."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.models import Connection, Tunnel, Profile
        print("✓ Models imported")

        from src.utils import validators
        print("✓ Validators imported")

        from src.core import SSHManager, TunnelManager
        print("✓ Core modules imported")

        from src.services import ProfileService, ConfigService, CredentialStore
        print("✓ Services imported")

        from src.gui import MainWindow
        print("✓ GUI imported")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models():
    """Test that models can be created."""
    print("\nTesting model creation...")

    try:
        from src.models import Connection, Tunnel
        from src.utils.constants import AuthMethod, TunnelType

        # Create a connection
        conn = Connection(
            host="localhost",
            port=22,
            username="testuser",
            password="testpass",
            auth_method=AuthMethod.PASSWORD
        )
        print(f"✓ Created connection: {conn}")

        # Create a tunnel
        tunnel = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=8080,
            remote_host="localhost",
            remote_port=80
        )
        print(f"✓ Created tunnel: {tunnel}")

        print("\n✅ Model creation successful!")
        return True

    except Exception as e:
        print(f"\n❌ Model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validators():
    """Test validators work."""
    print("\nTesting validators...")

    try:
        from src.utils.validators import validate_host, validate_port, validate_username

        # Test valid inputs
        is_valid, _ = validate_host("localhost")
        assert is_valid, "localhost should be valid"
        print("✓ Host validation works")

        is_valid, _ = validate_port(8080)
        assert is_valid, "Port 8080 should be valid"
        print("✓ Port validation works")

        is_valid, _ = validate_username("testuser")
        assert is_valid, "testuser should be valid"
        print("✓ Username validation works")

        # Test invalid inputs
        is_valid, error = validate_host("invalid;host")
        assert not is_valid, "Host with ; should be invalid"
        print("✓ Invalid host detection works")

        is_valid, error = validate_port(0)
        assert not is_valid, "Port 0 should be invalid"
        print("✓ Invalid port detection works")

        print("\n✅ Validators work correctly!")
        return True

    except Exception as e:
        print(f"\n❌ Validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("SSH Tunnel Manager - Quick Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Validators", test_validators()))

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")

    all_passed = all(r[1] for r in results)

    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Application is ready to use!")
        print("\nTo run the application:")
        print("  python src/main.py")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
