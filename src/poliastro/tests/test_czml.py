import pytest
from astropy import units as u
from astropy.coordinates import CartesianRepresentation
from astropy.time import TimeDelta
from numpy import insert as np_insert
from numpy.testing import assert_allclose

from poliastro.czml.extract_czml import CZMLExtractor
from poliastro.examples import iss, molniya
from poliastro.twobody.propagation import propagate


def test_czml_custom_packet():
    start_epoch = iss.epoch
    end_epoch = iss.epoch + molniya.period

    sample_points = 10

    ellipsoidr = [6373100, 6373100, 6373100]
    pr_map_url = (
        "https://upload.wikimedia.org/wikipedia/commons/c/c4/Earthmap1000x500compac.jpg"
    )

    extractor = CZMLExtractor(
        start_epoch, end_epoch, sample_points, ellipsoid=ellipsoidr, pr_map=pr_map_url
    )

    # Test that custom packet parameters where set correctly
    assert extractor.cust_czml[-1]["properties"]["ellipsoid"][0]["array"] == ellipsoidr
    assert extractor.cust_czml[-1]["properties"]["map_url"] == pr_map_url


def test_czml_add_orbit():
    start_epoch = iss.epoch
    end_epoch = iss.epoch + molniya.period

    sample_points = 10

    extractor = CZMLExtractor(start_epoch, end_epoch, sample_points)

    extractor.add_orbit(
        molniya, label_text="Molniya", label_fill_color=[125, 80, 120, 255]
    )
    extractor.add_orbit(iss, label_text="ISS", path_show=False)

    cords_iss = extractor.czml[1]["position"]["cartesian"]

    h_iss = (end_epoch - iss.epoch).to(u.second) / sample_points

    for i in range(sample_points):
        position_iss_test = propagate(iss, TimeDelta(i * h_iss))
        cords_iss_test = (
            position_iss_test.represent_as(CartesianRepresentation)
            .xyz.to(u.meter)
            .value
        )
        cords_iss_test = np_insert(cords_iss_test, 0, h_iss.value * i, axis=0)

        for j in range(4):
            assert_allclose(cords_iss[4 * i + j], cords_iss_test[j], rtol=1e-5)

    # Test label params and that the values between the two objects are not overwritten
    assert extractor.czml[0]["label"]["text"] == "Molniya"
    assert extractor.czml[1]["label"]["text"] == "ISS"
    assert extractor.czml[0]["label"]["fillColor"]["rgba"] == [125, 80, 120, 255]

    assert extractor.czml[1]["path"]["show"]["boolean"] is False


def test_czml_ground_station():
    start_epoch = iss.epoch
    end_epoch = iss.epoch + molniya.period

    sample_points = 10

    extractor = CZMLExtractor(start_epoch, end_epoch, sample_points)

    extractor.add_ground_station(
        [32 * u.degree, 62 * u.degree],
        id_name="GS",
        label_fill_color=[120, 120, 120, 255],
        label_text="GS test",
    )

    extractor.add_ground_station([0.70930 * u.rad, 0.40046 * u.rad], label_show=False)

    assert extractor.czml["GS0"]["id"] == "GS0"
    assert (
        extractor.czml["GS0"]["availability"]
        == "2013-03-18T12:00:00.000/2013-03-18T23:59:35.108"
    )
    assert extractor.czml["GS0"]["name"] == "GS"
    assert extractor.czml["GS0"]["label"]["fillColor"]["rgba"] == [120, 120, 120, 255]
    assert extractor.czml["GS0"]["label"]["text"] == "GS test"
    assert extractor.czml["GS0"]["label"]["show"] is True

    cords = [2539356.1623202674, 4775834.339416022, 3379897.6662185807]
    for i, j in zip(extractor.czml["GS0"]["position"]["cartesian"], cords):
        assert_allclose(i, j, rtol=1e-4)

    cords = [4456924.997008477, 1886774.8000006324, 4154098.219336245]
    for i, j in zip(extractor.czml["GS1"]["position"]["cartesian"], cords):
        assert_allclose(i, j, rtol=1e-4)


def test_czml_invalid_orbit_epoch_error():
    start_epoch = molniya.epoch
    end_epoch = molniya.epoch + molniya.period

    extractor = CZMLExtractor(start_epoch, end_epoch, 10)

    with pytest.raises(ValueError) as excinfo:
        extractor.add_orbit(iss, label_text="ISS", path_show=False)
    assert (
        "ValueError: The orbit's epoch cannot exceed the constructor's ending epoch"
        in excinfo.exconly()
    )