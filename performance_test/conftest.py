import pytest


def pytest_addoption(parser):
    parser.addoption('--csv-provider', default='standard')


@pytest.fixture
def csv_reader_factory(request):
    csv_provider = request.config.getoption('--csv-provider')
    if csv_provider == 'standard':
        import csv
        return csv.DictReader
    if csv_provider == 'scan':
        import csv_reader
        return csv_reader.DictReader
    if csv_provider == 'regex':
        pass #TODO
    assert False

