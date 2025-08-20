# Newsletter Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-08-20

### Added
- Validate schedule time before saving to Mailchimp (#82)
- Mailchimp: Request 1000 audience segments and select only "saved" segments (#84)
- Development tooling with `uv` (#85)
- Support for Django 5.2, Wagtail 7.0 and 7.1. (#85)
- Add extra context to `get_newsletter_html` (#88)

### Removed

- Support for Python 3.9, Django 5.0, Wagtail 5.2 and 6.4. (#85)

## [0.2.2] - 2025-04-16

### Added

- Support for Wagtail 6.4 and Python 3.13 (#74)

### Changed

- Bump minimum `mrml` version to `0.2` (#72)
- Extract get_newsletter_subject method (#77)
- `{% newsletter_static %}` template tag (#79)

### Removed

- Support for Python 3.8 (#72)
- Support for Wagtail 6.2 (#74)

## [0.2.1] - 2024-09-06

### Added

- Schedule campaign sending (#53).

### Changed

- Additional error handling (#56).

## [0.2.0] - 2024-08-02

Initial release.

## [0.1.0] - 2024-06-17

Test pre-release.

<!-- TEMPLATE - keep below to copy for new releases -->
<!--


## [x.y.z] - YYYY-MM-DD

### Added

- ...

### Changed

- ...

### Removed

- ...

-->
