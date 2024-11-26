# Feature Overview

This chapter aims to give a high level overview of what features the plugin supports, including known limitations, so as to set realistic expectations on how the plugin can be used.

For detailed usage examples, see `How-to Guides` instead.
See the [REST API documentation](https://staging-docs.pulpproject.org/pulp_deb/restapi/) for an exhaustive feature reference.

## Core Features

### Repository Synchronization

Synchronizing upstream repositories is one of two ways to obtain content for the `pulp_deb` plugin.
See [package uploads](#package-uploads) for the other.
The aim is for the plugin to be able to synchronize (and publish) arbitrary (valid) APT repositories.
This also includes repositories using [flat repository format](https://wiki.debian.org/DebianRepository/Format#Flat_Repository_Format).

When synchronizing an upstream repository, only content supported by the `pulp_deb` plugin is downloaded. This includes:

- `Release`, `InRelease`, and `Release.gpg` metadata files.
- Binary package indices, aka `Packages` files.
- Any `.deb` binary packages referenced by any package indices being synced.
- (optionally) Installer package indices, the associated `.udeb` installer packages, as well as some other installer file types.

Things that are not synchronized:

- Source indices and source packages.
- Language and translation files.
- Anything else not explicitly mentioned above.

If and how this synchronized content is ultimately used, is dependent on the publisher and its options.
For more information see [verbatim publishing](#verbatim-publishing) and [APT publishing](#apt-publishing) below.

#### Filtered Synchronization

It is possible to synchronize only a subset of a given upstream repository by specifying a set of distributions (aka releases), components, and architectures to synchronize.
Specifying the desired distributions is mandatory, while not specifying any components or architectures is interpreted as: "synchronize all that are available".

#### Signature Verification

!!! note
    For APT repositories, only the `Release` file of each distribution is signed.
    This file contains various checksums for all other metadata files contained within the distribution, which in turn contain the checksums of the packages themselves.
    As a result, signing the `Release` file is sufficient to guarantee the integrity of the entire distribution.


You may provide your remotes with the relevant (public) GPG key for `Release` file signature verification.
When synchronizing an upstream repository using signature verification, any metadata files that cannot be verified are discarded.
If no relevant metadata files are left, a `NoReleaseFile` error is thrown and the sync fails.

### Package Uploads

Rather than synchronizing upstream repositories, it is also possible to upload `.deb` package files to the `pulp_deb` plugin in a variety of ways.
See the corresponding [workflow documentation](https://staging-docs.pulpproject.org/pulp_deb/docs/user/guides/upload/#upload-and-manage-content) for more information.
In general, uploading content works the same way as for any other Pulp plugin, so you may also wish to consult the [pulpcore upload documentation](https://staging-docs.pulpproject.org/pulpcore/docs/user/guides/upload-publish/).


### Hosting APT Repositories

Once you have obtained some content via synchronization, or upload, you will want to publish and distribute this content, so that your clients may consume your hosted APT repositories.

The default way to do so is to use the `pulp_deb` APT publisher.
This publisher will generate new metadata for any `.deb` packages stored in your Pulp repository.
Any upstream metadata, installer files, and installer packages will be ignored.
The APT publisher will publish all the distributions (aka releases), components, and architectures, that were synchronized to the Pulp repository being published (or else created during package upload).
It will also use a default `pool/` folder structure regardless of the package file locations used by the relevant upstream repository.

This approach guarantees a consistent set of packages and metadata is presented to your clients using the latest APT repository format specification.
It also allows you to sign the newly generated metadata using your own signing key.

An alternative is to use the `pulp_deb` [verbatim publisher](#verbatim-publishing).

#### Metadata Signing

The `pulp_deb` plugin allows you to sign any `Release` files generated by the APT publisher by providing it with a signing service of type `AptReleaseSigningService` at the time of creation.
It is also possible to use different signing services for different distributions within your APT repositories.

## Advanced Features

### Verbatim Publishing

!!! note
    Even though the interface is very different, the verbatim publisher is comparable to `pulp_rpm`'s "full mirror" sync feature.


The verbatim publisher is an alternative to the `pulp_deb` plugin's main [APT publisher](#apt-publishing).
It will recreate an exact copy of the subset of an upstream repo that was synchronized into Pulp.
In other words, every synchronized file, including the upstream metadata will use the exact same relative path it had in the upstream repository.

**Advantages:**

- Upstream `Release` file signatures are retained, so clients can verify using the same keys as for the upstream repository.
- No new metadata is generated, so the verbatim publisher is much faster than the APT publisher.
- The verbatim publisher is the only way to publish synchronized installer files and packages.

**Disadvantages:**

- Since it relies on upstream metadata, it only works for synced content.
- It is not possible to sign a verbatim publication using your own [signing services](#metadata-signing).
- Since the upstream repo is mirrored exactly, any errors in the upstream repo are retained.
- In some cases the upstream metadata may be inconsistent with what was synced into Pulp.

### Advanced Copy

The plugin provides an advanced copy feature for moving packages between repositories.
Using this feature, it is possible to specify a set of packages to be copied from one Pulp repository to another, without having to manually specify the structure content that tells Pulp what packages go into what release component.
That way, the repository version created in the target repository, can be meaningfully published using the [APT publisher](#apt-publishing), without relying on the "simple publishing" workaround.

We are also planning to expand the advanced copy feature with a [dependency solving](#dependency-solving) mechanism in the future.

### ApyByHash

AptByHash is a feature that mitigates commonplace 'Hash Sum Mismatch' errors during an 'apt-get-update'.
It adds the checksum of the package metadata to the the packages' names.
These files are then stored within a 'by-hash' directory within each release architecture in the specified debian repository.
The client will then use the filename to identify the expected checksum and download a file whose name matches the checksum.

Please note that this feature is disabled by default and should be enabled prior to use.
To do this, set `APT_BY_HASH = True` in `/pulp_deb/app/settings.py`.

In addition, you are responsible for setting up a reverse proxy with cache in order to cache the by-hash files.

### Import/Export

The `pulp_deb` plugin implements the pulpcore Import/Export API. Which allows you to import and export repositories.
See also the [pulpcore import-export docs](https://staging-docs.pulpproject.org/pulpcore/docs/admin/guides/import-export-repos/).

### Source Packages

The `pulp_deb` plugin is able to sync and publish [Debian source packages](https://wiki.debian.org/Packaging/SourcePackage).

## Roadmap and Experimental

!!! warning
    This section describe features that are either planned for the future, or exist only in an experimental state.
    These features may lack expected functionality, or break unexpectedly.
    The API may still change in non-backwards compatible ways.

### Installation from Synced Content

It is currently possible to synchronize installer indices and packages and publish them using the [verbatim publisher](#verbatim-publishing).
However, there is no actual test coverage for installing Debian or Ubuntu hosts from a so published repository using the debian-installer.
We have also received feedback that the feature is currently broken since `pulp_deb` currently lacks the ability to synchronize language and translation files which are needed for the debian-installer.

!!! note
    There is not yet any firm time table for when this might be worked on.
    The next step is to solve the [translation file issue](https://github.com/pulp/pulp_deb/issues/408).

### Dependency Solving

It is planned to expand the [advanced copy](#advanced-copy) feature with a dependency solving mechanism analogous to the one provided by `pulp_rpm`.
The idea is to make it possible to specify a list of packages and automatically copy them *and their entire dependency trees* into a target repo.

!!! note
    There is not yet any firm time table for when this might be worked on.
    See the [dependency solving issue](https://github.com/pulp/pulp_deb/issues/386) for any new developments.


### Domain and RBAC (Multi-Tenancy)

There have been multiple requests for this feature in `pulp_deb`.

!!! note
    The plugin maintainers have no plans to implement this.
    If you are interested in contributing to the development of this feature, please get in touch with us via the [multi tenancy feature request](https://github.com/pulp/pulp_deb/issues/860).
