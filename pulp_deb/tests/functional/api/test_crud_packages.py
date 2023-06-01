"""Tests that perform actions over packages."""
import uuid
import pytest

from pulp_smash import utils

from pulp_deb.tests.functional.constants import (
    DEB_PACKAGE_RELPATH,
    DEB_SOURCE_PACKAGE_RELPATH,
    DEB_SOURCE_PACKAGE_ARTIFACTS,
)
from pulp_deb.tests.functional.utils import get_local_package_absolute_path


def create_source_package(deb_artifact_factory, deb_package_factory):
    for artifact_name in DEB_SOURCE_PACKAGE_ARTIFACTS:
        attrs = {
            "file": get_local_package_absolute_path(artifact_name),
        }
        artifact = deb_artifact_factory(**attrs)
        if artifact_name == DEB_SOURCE_PACKAGE_RELPATH:
            dsc_artifact = artifact

    attrs = {
        "deb_source_package": {
            "relative_path": DEB_SOURCE_PACKAGE_RELPATH,
            "artifact": dsc_artifact.pulp_href,
        },
    }
    package = deb_package_factory(**attrs)

    return package


def create_binary_package(deb_artifact_factory, deb_package_factory):
    attrs = {
        "relative_path": DEB_PACKAGE_RELPATH,
        "file": get_local_package_absolute_path(DEB_PACKAGE_RELPATH),
    }
    package = deb_package_factory(**attrs)

    return package


@pytest.mark.parallel
@pytest.mark.parametrize("create_package, apt_package_api, package_relpath", [
    (create_source_package, "source", DEB_SOURCE_PACKAGE_RELPATH),
    (create_binary_package, "binary", DEB_PACKAGE_RELPATH),
], indirect=["apt_package_api"])
def test_create_package(
    create_package,
    apt_package_api,
    package_relpath,
    deb_artifact_factory,
    deb_package_factory,
):
    """Verify all allowed CRUD actions are working and the ones that don't exist fail."""
    # Create a package and verify its attributes
    package = create_package(deb_artifact_factory, deb_package_factory)
    assert package.relative_path == package_relpath

    # Verify that only one package with this relative path exists
    package_list = apt_package_api.list(relative_path=package.relative_path)
    assert package_list.count == 1

    # Verify that reading the package works and has the same attributes
    package = apt_package_api.read(package.pulp_href)
    assert package.relative_path == package_relpath

    # Verify that partial update does not work for packages
    with pytest.raises(AttributeError) as exc:
        apt_package_api.partial_update(package.pulp_href, relative_path=str(uuid.uuid4()))
    assert "object has no attribute 'partial_update'" in exc.value.args[0]

    # Verify that update does not work for packages
    with pytest.raises(AttributeError) as exc:
        apt_package_api.update(package.pulp_href, relative_path=str(uuid.uuid4()))
    assert "object has no attribute 'update'" in exc.value.args[0]

    # Verify that delete does not work for packages
    with pytest.raises(AttributeError) as exc:
        apt_package_api.delete(package.pulp_href)
    assert "object has no attribute 'delete'" in exc.value.args[0]

@pytest.mark.parametrize("create_package, apt_package_api, package_relpath", [
    (create_source_package, "source", DEB_SOURCE_PACKAGE_RELPATH),
    (create_binary_package, "binary", DEB_PACKAGE_RELPATH),
], indirect=["apt_package_api"])
def test_same_sha256_same_relative_path_no_repo(
    create_package,
    apt_package_api,
    package_relpath,
    deb_artifact_factory,
    deb_package_factory,
):
    """Test whether uploading the same package works and that it stays unique."""
    # Create the first package and verify its attributes
    package_1 = create_package(deb_artifact_factory, deb_package_factory)
    assert package_1.relative_path == package_relpath

    # Create the second package and verify it has the same href as the first one
    package_2 = create_package(deb_artifact_factory, deb_package_factory)
    assert package_2.pulp_href == package_1.pulp_href
    assert apt_package_api.read(package_1.pulp_href).pulp_href == package_2.pulp_href

    # Verify the package is one
    package_list = apt_package_api.list(relative_path=package_relpath)
    assert package_list.count == 1


def test_structured_package_upload(
    apt_package_api,
    deb_get_repository_by_href,
    deb_package_factory,
    deb_repository_factory,
):
    """Test whether uploading a structured package works and creates the correct paths."""
    attrs = {
        "file": get_local_package_absolute_path(DEB_PACKAGE_RELPATH),
        "relative_path": DEB_PACKAGE_RELPATH,
        "distribution": utils.uuid4(),
        "component": utils.uuid4(),
    }

    repository = deb_repository_factory()
    assert repository.latest_version_href.endswith("/0/")
    attrs["repository"] = repository.pulp_href

    deb_package_factory(**attrs)
    repository = deb_get_repository_by_href(repository.pulp_href)
    assert repository.latest_version_href.endswith("/1/")

    package_list = apt_package_api.list(relative_path=DEB_PACKAGE_RELPATH)
    assert package_list.count == 1

    results = package_list.results[0]
    assert results.relative_path == attrs["relative_path"]
