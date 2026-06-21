Testing Guide
=============

Markers
-------

``web``
    Page and route tests.

``buttons``
    Pull Data and Update Analysis endpoint tests.

``analysis``
    Formatting tests.

``db``
    Database tests.

``integration``
    End-to-end tests.

Selectors
---------

``data-testid="pull-data-btn"``

``data-testid="update-analysis-btn"``

Fixtures
--------

Tests use ``monkeypatch`` to fake scraper, loader, database connections, and busy state.