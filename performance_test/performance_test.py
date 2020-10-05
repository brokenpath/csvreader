import pytest


@pytest.fixture(scope='module')
def csv_file(tmp_path_factory):
    file_path = tmp_path_factory.mktemp('data') / 'data.csv'
    line = '1234567890,abcdefghijklmnopqrstuvvxyz,abcdefghijklmnopqrstuvvxyz\n'
    with open(str(file_path), 'w') as stream:
        stream.write('a,b,c\n')
        for _ in range(300000):
            stream.write(line)
    yield file_path
    file_path.unlink()


def read_csv_file(csv_reader_factory, csv_file):
    with open(str(csv_file)) as stream:
        reader = csv_reader_factory(stream)
        for record in reader:
            pass


def test_performance(benchmark, csv_reader_factory, csv_file):
    benchmark(read_csv_file, csv_reader_factory, csv_file)

