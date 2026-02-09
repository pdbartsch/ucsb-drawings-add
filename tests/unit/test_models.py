# from pandas import isnull
from flaskdraw.models import User, Drawfile, Drawloc, Drawings
from flask_bcrypt import generate_password_hash


def test_new_user(new_user):
    """
    GIVEN a User model and new_user defined in conftest.py
    WHEN a new User is created
    THEN check the username, email and hashed_password are correctly defined
    """

    hashed_password = generate_password_hash(new_user.password).decode("utf-8")
    assert new_user.username == "testuser"
    assert new_user.email == "testuser@testing.com"
    assert hashed_password != new_user.password


def test_new_location(new_location):
    """
    GIVEN Drawloc model and new_location defined in conftest.py
    WHEN a new location is created
    THEN check the fields are correctly defined
    """

    assert new_location.locnum == 506
    assert new_location.locdescrip == "Interactive Learning Pavillion"


def test_new_project(new_project):
    """
    GIVEN Drafile model and new_project defined in conftest.py
    WHEN a new project is created
    THEN check the fields are correctly defined
    """

    assert new_project.locnum == 525
    assert new_project.drawnum == 701
    assert new_project.projectmngr == "Paul David Bartsch"
    assert new_project.mainconsult == "Landon Bartsch"
    assert new_project.title == "Parker's New Castle"
    assert new_project.projectnum == "548FM5"


def test_new_drawing(new_drawing):
    """
    GIVEN Drawings model and new_drawing defined in conftest.py
    WHEN a new project is created
    THEN check the fields are correctly defined
    """


    assert new_drawing.id == 1
    assert new_drawing.newname == "34_348_CIV_0_26726.pdf"
    assert new_drawing.locnum == 34
    assert new_drawing.drawnum == 348
    assert new_drawing.project_title == "PARKING LOT 38"
    assert new_drawing.project_number == "FM805/18-7"
    assert new_drawing.project_year == 2004
    assert new_drawing.sheet_title == "CIVIL SITE PLAN"
    assert new_drawing.sheet_number == "C_1_5"
    assert new_drawing.discipline == "CIVIL"
    assert new_drawing.drawing_version == "RECORD"
    assert (
        new_drawing.notes
        == "Original file name was: R_G8_0034_0348_NO_0000.TIF Original drawer was: 31"
    )
    assert new_drawing.physical_location == "Original Ucsb Drawer 31"

