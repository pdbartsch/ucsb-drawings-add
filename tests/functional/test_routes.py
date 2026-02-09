import os
from urllib import response
from flask import url_for


def test_landing_aliases(client):
    # tests that aliases return same results
    landing = client.get("/")
    assert client.get(url_for("bp_main.index")).data == landing.data


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get(url_for("bp_main.index"))
    html = response.data.decode()
    assert response.status_code == 200
    assert 'href="/locations/">Locations</a>' in html, "location navbar link check"
    assert 'href="/projects/">Projects</a>' in html, "projects navbar link check"
    assert (
        'href="/search_drawings/">Drawings</a>' in html
    ), "search drawings navbar link check"
    assert 'href="/login">Admin Login</a>' in html, "login navbar link check"
    assert "nav-item nav-link" in html, "navbar class check"


# test for sql injection
def test_login_page_post_sql_injection(client):
    response = client.post(
        url_for("bp_users.login"),
        follow_redirects=True,
        data={
            "username": "admin' or '1'='1",
            "email": "admin' or '1'='1",
            "password": "admin",
        },
    )
    assert response.status_code == 200
    assert b"Login" in response.data, "login page check"
    assert (
        b"Login unsuccessful. Please check email and password." in response.data
    ), "login error check"


def test_home_page_post(client):
    """
    GIVEN a Flask application
    WHEN the '/' page is posted to (POST)
    THEN check that a '405' status code is returned
    """
    response = client.post(url_for("bp_main.index"))
    assert response.status_code == 405, "this home page shouldn't allow post requests"
    assert b"All Projects:" not in response.data, "if this failed then the page loaded"


def test_location_list_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the locations (/locs/) page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get(url_for("bp_locations.locations"), follow_redirects=True)
    assert response.status_code == 200
    assert b"Location Categories:" in response.data


def test_drawings_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the drawings page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get(url_for("bp_drawings.drawings"), follow_redirects=True)
    assert response.status_code == 200
    assert b"Result of drawing search:" in response.data, "Home page header check"


def test_list_projects_one_locnum(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/locnum' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get("/projects/525", follow_redirects=True)
    assert response.status_code == 200
    assert b"UCSB Drawing #525-" in response.data, "UCSB Drawing Numbers header check"


def test_list_single_project(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/locnum/drawnum' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get("/projects/525/120", follow_redirects=True)
    assert response.status_code == 200
    assert (
        b"UCSB Drawing #525-120" in response.data
    ), "UCSB Drawing Numbers header check"


def test_drawing_search_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the drawing search page is requested (GET)
    THEN check that the response is valid
    """

    response = client.get(url_for("bp_drawings.search_drawings"))
    assert response.status_code == 200
    assert b"Search For Drawings:" in response.data, "Home page header check"


# requires login
def test_register_page_get(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the register page is requested (GET)
    THEN check that the response is valid
    """

    response = client.get(url_for("bp_users.register"))
    assert response.status_code == 200


def test_register_page_post(client):
    response = client.post(url_for("bp_users.register"), follow_redirects=True)
    assert response.status_code == 200


def test_login_page_get(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the login page is requested (GET)
    THEN check that the response is valid
    """

    response = client.get(url_for("bp_users.login"))
    assert response.status_code == 200


def test_login_page_post(client):
    response = client.post(url_for("bp_users.login"), follow_redirects=True)
    assert response.status_code == 200


def test_not_logged_in(client):
    """
    GIVEN a Flask application configured for testing and no user logged in
    WHEN the '/' page is requested (GET)
    THEN check that the response doesn't contain protected links
    """
    response = client.get(url_for("bp_main.index"))

    assert b"Add Drawing" not in response.data, "Protected Navbar Link Check 02"
    assert b"Add Location" not in response.data, "Protected Navbar Link Check 03"


def test_add_location(client):
    response = client.get(url_for("bp_locations.add_loc"), follow_redirects=True)
    assert response.status_code == 200


def test_logout(client):
    response = client.get(url_for("bp_users.logout"), follow_redirects=True)
    assert response.status_code == 200


def test_drawproj_page(client):
    response = client.get(
        url_for("bp_drawings.location_set", locnum=525), follow_redirects=True
    )
    assert response.status_code == 200


def test_drawproj_drawings_locnum(client):
    response = client.get(
        url_for("bp_drawings.drawings", locnum=525), follow_redirects=True
    )
    assert response.status_code == 200


def test_drawproj_drawings_draw_n_locnums(client):
    response = client.get(
        url_for("bp_drawings.drawings", drawnum=101, locnum=525), follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        b"Your query returned no results" not in response.data
    ), "Should return results"


def test_drawproj_drawings_nonsense(client):
    response = client.get(
        url_for("bp_drawings.drawings", nonsense=101), follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        b"Your query returned no results" in response.data
    ), "Should NOT return results"
