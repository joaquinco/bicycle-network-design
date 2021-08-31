from unittest import TestCase

from bcnetwork.solution import Solution
from bcnetwork.draw import draw

from .utils import get_test_model, get_resource_path


class DrawTestCase(TestCase):
    def setUp(self):
        self.model = get_test_model()
        self.solution = Solution(
            stdout_file=get_resource_path('stdout.cbc'), solver='cbc')

    def test_draw(self):
        draw(self.model)

    def test_draw_with_solution(self):
        draw(self.model, solution=self.solution)
