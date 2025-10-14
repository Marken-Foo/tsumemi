from tsumemi.src.tsumemi import problem as pb, timer
from tsumemi.src.tsumemi.problem_list.problem_list_model import ProblemList


def get_num_total(problem_list: ProblemList) -> int:
    return len(problem_list)


def get_num_correct(problem_list: ProblemList) -> int:
    return len(problem_list.filter_by_status(pb.ProblemStatus.CORRECT))


def get_num_wrong(problem_list: ProblemList) -> int:
    return len(problem_list.filter_by_status(pb.ProblemStatus.WRONG))


def get_num_skipped(problem_list: ProblemList) -> int:
    return len(problem_list.filter_by_status(pb.ProblemStatus.SKIP))


def get_total_time(problem_list: ProblemList) -> timer.Time:
    return problem_list.filter_by_status(
        pb.ProblemStatus.CORRECT, pb.ProblemStatus.WRONG, pb.ProblemStatus.SKIP
    ).get_total_time()


def get_fastest_problem(problem_list: ProblemList) -> pb.Problem | None:
    return problem_list.get_fastest_problem()


def get_slowest_problem(problem_list: ProblemList) -> pb.Problem | None:
    return problem_list.get_slowest_problem()
