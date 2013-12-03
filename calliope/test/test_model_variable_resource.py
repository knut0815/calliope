from __future__ import print_function
from __future__ import division

import pytest
import tempfile

import common
from common import assert_almost_equal


class TestModel:
    @pytest.fixture(scope='module')
    def model(self):
        nodes = """
            nodes:
                1:
                    level: 1
                    within:
                    techs: ['demand']
                    override:
                        demand:
                            constraints:
                                r: -10
                sub1:
                    level: 0
                    within: 1
                    techs: ['ccgt']
                    override:
                        ccgt:
                            constraints:
                                e_cap_max: 9
                sub2:
                    level: 0
                    within: 1
                    techs: ['pv']
                    override:
                        pv:
                            x_map: 'demand: sub2'
                            constraints:
                                e_cap_max: 9
                                r: file=demand-sin_r.csv
                                r_scale_to_peak: 5

            links:
        """
        config_run = """
            input:
                techs: {techs}
                nodes: {nodes}
                path: '{path}'
            output:
                save: false
            subset_t: ['2005-01-01', '2005-01-02']
        """
        with tempfile.NamedTemporaryFile() as f:
            f.write(nodes)
            f.read()
            model = common.simple_model(config_run=config_run,
                                        config_nodes=f.name)
        model.run()
        return model

    def test_model_solves(self, model):
        assert str(model.results.Solution.Status) == 'optimal'

    def test_model_balanced(self, model):
        df = model.get_system_variables()
        assert_almost_equal(df.ix[0, 'pv'], 7.5, tolerance=0.01)
        assert (df['pv'] + df['ccgt'] == -1 * df['demand']).all()

    def test_model_costs(self, model):
        df = model.get_costs()
        assert_almost_equal(df.at['lcoe', 'total', 'ccgt'], 0.1,
                            tolerance=0.001)