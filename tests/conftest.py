import os
import pytest
from flaskdraw import create_app
from flaskdraw.config import TestConfig
from flaskdraw.models import User, Drawfile, Drawings, Drawloc


@pytest.fixture
def app():
    app = create_app(TestConfig)

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(scope="module")
def new_user():
    user = User(
        username="testuser", email="testuser@testing.com", password="FlaskIsAwesome"
    )
    return user


@pytest.fixture(scope="module")
def new_location():
    location = Drawloc(locnum=506, locdescrip="Interactive Learning Pavillion")
    return location



@pytest.fixture(scope="module")
def new_project():
    project = Drawfile(
        locnum = 525, drawnum = 701, projectmngr = 'Paul David Bartsch', 
        mainconsult = 'Landon Bartsch', title = "Parker's New Castle", projectnum="548FM5"
        )
    return project

@pytest.fixture(scope="module")
def new_drawing():
    drawing = Drawings(
        id=1, newname='34_348_CIV_0_26726.pdf', locnum=34, drawnum=348, 
        project_title='PARKING LOT 38', project_number="FM805/18-7", project_year=2004, sheet_title='CIVIL SITE PLAN', 
        sheet_number='C_1_5', discipline='CIVIL', drawing_version='RECORD', 
        notes='Original file name was: R_G8_0034_0348_NO_0000.TIF Original drawer was: 31', physical_location='Original Ucsb Drawer 31'
        )
    return drawing
