from time import time
from unittest.mock import patch
import numpy as np
import pytest
from baynet.structure import Graph
from baynet.parameters import ConditionalProbabilityTable, _sample_cpt
from .utils import test_dag


def test_CPT_init():
    dag = test_dag()
    dag.vs['levels'] = 2
    cpt = ConditionalProbabilityTable(dag.vs[1])
    assert cpt._array.shape == (2, 2, 2)
    assert np.allclose(cpt._array, 0)

    dag.add_vertex("E")
    with pytest.raises(ValueError):
        ConditionalProbabilityTable(dag.vs[dag.get_node_index("E")])

    dag.add_edge("E", "A")
    with pytest.raises(ValueError):
        ConditionalProbabilityTable(dag.vs[dag.get_node_index("A")])


def test_CPT_rescale():
    dag = test_dag()
    for n_levels in [1, 2, 3, 4]:
        dag.vs['levels'] = n_levels
        cpt = ConditionalProbabilityTable(dag.vs[1])
        cpt.rescale_probabilities()
        # Check cumsum is working properly
        for i in range(cpt._levels):
            assert np.allclose(cpt._array[:, :, i], (i + 1) / cpt._levels)
    cpt._array = np.random.uniform(size=(3, 3, 3))
    cpt.rescale_probabilities()
    for i in range(3):
        for j in range(3):
            # Check last value in each CPT 'row' is 1 (double checking cumsum with random init)
            assert np.isclose(np.sum(cpt[i, j, -1]), 1)
            # and each value is larger than the previous
            assert cpt[i, j, 0] <= cpt[i, j, 1] <= cpt[i, j, 2]


def test_CPT_sample_exceptions():
    dag = test_dag()
    dag.vs['levels'] = 2
    cpt = ConditionalProbabilityTable(dag.vs[1])
    with pytest.raises(ValueError):
        cpt.sample(None)
    cpt.rescale_probabilities()
    with pytest.raises(ValueError):
        cpt.sample(np.zeros((10, 10))[[]])


def test_sample_cpt():
    dag = test_dag()
    dag.vs['levels'] = 2
    cpt = ConditionalProbabilityTable(dag.vs[1])
    cpt._array[0, 0, :] = [0.5, 0.5]
    cpt._array[0, 1, :] = [1.0, 0.0]
    cpt._array[1, 0, :] = [0.0, 1.0]
    cpt._array[1, 1, :] = [0.5, 0.5]
    cpt.rescale_probabilities()

    parent_values = np.array([[0, 0], [0, 0], [0, 1], [0, 1], [1, 0], [1, 0], [1, 1], [1, 1]])
    parent_values_tuples = list(map(tuple, parent_values))

    random_vector = np.repeat([[0.1, 0.9]], 4, axis=0).flatten()

    expected_output = np.array([0, 1, 0, 0, 1, 1, 0, 1])

    assert np.all(_sample_cpt(cpt._array, parent_values_tuples, random_vector) == expected_output)
    np.random.seed(0)  # TODO: replace with mocking np.random.normal
    assert np.all(cpt.sample(parent_values) == [1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0])


def time_sample_cpt():
    n = 1_000_000
    levels = 3

    dag = Graph.from_modelstring("[A|B:C:D:E:F:G:H:I:J:K][B][C][D][E][F][G][H][I][J][K]")
    dag.vs['levels'] = levels
    cpt = ConditionalProbabilityTable(dag.vs[0])
    cpt.rescale_probabilities()
    parent_values = np.random.randint(0, levels, size=(n, 2))
    parent_values = list(map(tuple, parent_values))
    random_vector = np.random.uniform(size=(n))

    start = time()
    _sample_cpt(cpt._array, parent_values, random_vector)
    end = time()
    print(end - start)


if __name__ == "__main__":
    time_sample_cpt()