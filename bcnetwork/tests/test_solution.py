from unittest import TestCase

from bcnetwork.solution import Solution
from bcnetwork.bunch import Bunch


class SolutionTestCase(TestCase):
    def setUp(self):
        self.file = 'bcnetwork/tests/resources/stdout.cbc'

    def test_solution_creation(self):
        sol = Solution(stdout_file=self.file)

        self.assertIsNotNone(sol)

    def test_solution_data(self):
        sol = Solution(stdout_file=self.file)

        self.assertIsNotNone(sol.data)
        self.assertGreater(len(sol.data), 0)

    def test_budget_used(self):
        sol = Solution(stdout_file=self.file)

        self.assertGreater(sol.budget_used, 0)

    def test_total_demand_transfered(self):
        sol = Solution(stdout_file=self.file)

        self.assertGreater(sol.total_demand_transfered, 0)

    def test_data_access(self):
        sol = Solution(stdout_file=self.file)

        self.assertIsInstance(sol.data, Bunch)
        self.assertIsInstance(sol.data.shortest_paths[0], Bunch)
