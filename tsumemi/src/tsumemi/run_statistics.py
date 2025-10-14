from tsumemi.src.tsumemi import timer
from tsumemi.src.tsumemi.problem import Problem
from tsumemi.src.tsumemi.problem_list import problem_list_stats as pliststats
from tsumemi.src.tsumemi.problem_list.problem_list_model import ProblemList


class RunStatistics:
    def __init__(self, problem_list: ProblemList, directory_name: str) -> None:
        self.directory_name = directory_name
        self.total_problems = pliststats.get_num_total(problem_list)
        self.total_correct = pliststats.get_num_correct(problem_list)
        self.total_wrong = pliststats.get_num_wrong(problem_list)
        self.total_skipped = pliststats.get_num_skipped(problem_list)
        self.total_time = pliststats.get_total_time(problem_list)
        self.slowest_problem: Problem | None = pliststats.get_slowest_problem(
            problem_list
        )
        self.fastest_problem: Problem | None = pliststats.get_fastest_problem(
            problem_list
        )

    @property
    def total_seen(self) -> int:
        return self.total_correct + self.total_wrong + self.total_skipped

    @property
    def average_time_per_problem(self) -> timer.Time:
        if self.total_seen == 0:
            return timer.Time(0)
        else:
            return timer.Time(self.total_time.seconds / self.total_seen)
