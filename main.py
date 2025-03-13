import argparse
from enums import CheckersResult, CheckersRules
from interface import GameInterface
from quantum_checkers import Checkers
import time
import players
import os
import glob
import random
import trueskill
import statistics


def generate_matches(agents):
    matches = []
    num_agents = len(agents)

    for i in range(num_agents):
        for j in range(i + 1, num_agents):
            # if(agents[i] == agents[j]):
            #     continue
            matches.append(
                (agents[i], agents[j])
            )  # Agent i as player 1, Agent j as player 2
            matches.append(
                (agents[j], agents[i])
            )  # Agent j as player 1, Agent i as player 2
    return matches


def empty_attempts_folder():
    files = glob.glob("./attempts/*")
    for f in files:
        os.remove(f)

    files = glob.glob("./screenshots/*")
    for f in files:
        os.remove(f)


def empty_attempts():
    files = glob.glob("./attempts/*")
    for f in files:
        os.remove(f)


def write_attempt(idx, attempt_str):
    temp = open(f"./attempts/log_{idx}.txt", "a")
    temp.write(attempt_str)
    temp.close()


def get_argument_parser_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--num_rows",
        help="The number of rows of the checkboard. INT",
        default=8,
        type=int,
    )
    parser.add_argument(
        "--num_columns",
        help="The number of columns of the checkboard. INT",
        default=8,
        type=int,
    )
    parser.add_argument(
        "--num_vertical_pieces",
        help="The number of rows that are filled with checkerpieces. INT",
        default=3,
        type=int,
    )
    parser.add_argument(
        "--sim_q",
        help="Simulating quantum or actually use quantum mechanics. TRUE if you want to simulate quantum.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--disable-GUI",
        help="If GUI is enabled. True or False",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--p1", help="Select agent for player 1 to use.",
        default="human",
        choices=["human", "heuristic", "random"]
    )
    parser.add_argument(
        "--p2", help="Select agent for player 2 to use.",
        default="human",
        choices=["human", "heuristic", "random"]
    )
    parser.add_argument(
        "--rule-set", help="What rule set to use. With 'superposition', no "
        "entanglement is possible. With 'entanglement', both superposition "
        "and entanglement are possible",
        default="entanglement",
        choices=["classical", "superposition", "entanglement"]
    )
    parser.add_argument(
        "--results-file", help="The filename to save the results in",
        default="results.txt")
    parser.add_argument(
        "--iterations", help="The amount of iterations for the experiment",
        default=500,
        type=int)
    parser.add_argument(
        "--do-average-moves-and-time-experiment",
        help="Run experiments to determine the average moves and times in "
        "different versions on different board sizes", action="store_true",
        default=False)
    return parser.parse_args()


def run_average_moves_and_times_experiment(args):
    file = open(args.results_file, "w")
    file.close()
    file = open(args.results_file, "a")
    rules = [CheckersRules.CLASSICAL, CheckersRules.QUANTUM_V1,
             CheckersRules.QUANTUM_V2]
    # rules = [CheckersRules.QUANTUM_V2]
    sizes = [5, 6, 7, 8, 10, 12, 14]
    args.num_vertical_pieces = 1
    args.sim_q = False
    args.disable_GUI = True
    # just mcts agents
    agents = ["random", "random"]

    for draw_rule_enabled in [True, False]:
        if draw_rule_enabled:
            file.write('\n\nDraw rule enabled\n\n')
        else:
            file.write('\n\nNo draw rule\n\n')
        for rule in rules:
            moves_list = []
            moves_sd_list = []
            times_list = []
            times_sd_list = []
            for size in sizes:
                print(f'Rule {rule} on size {size}')
                times = []
                results = []
                number_of_moves = []
                avg_mcts_time = []
                iterations = args.iterations
                for k in range(iterations):
                    if k % 250 == 0 and k != 0:
                        print(
                            f"Iteration: {k+1} at "
                            f"{time.strftime('%H:%M', time.localtime())}"
                        )
                    sd = random.randint(0, 100000000000000000)
                    # sd = 4271756581358815
                    random.seed(sd)
                    random.shuffle(agents)
                    matches = generate_matches(agents)
                    # print("Matches:", matches)
                    for i, j in matches:
                        white_mcts = False
                        black_mcts = False
                        args1 = None
                        args2 = None
                        p1 = players.random_bot()
                        p2 = players.random_bot()

                        start_t = time.time()
                        checkers = Checkers(
                            num_vertical=size,
                            num_horizontal=size,
                            num_vertical_pieces=args.num_vertical_pieces,
                            SIMULATE_QUANTUM=args.sim_q,
                            rules=rule,
                            draw_after_40_rule_enabled=draw_rule_enabled
                        )
                        game = GameInterface(
                            checkers,
                            white_player=p1,
                            black_player=p2,
                            GUI=(not args.disable_GUI),
                            white_mcts=white_mcts,
                            black_mcts=black_mcts,
                            args_1=args1,
                            args_2=args2,
                            print=False,
                            attempt=k,
                        )
                        result, num_moves, avg_time, single_movetypes = game.play()
                        results.append(result)
                        number_of_moves.append(num_moves)
                        avg_mcts_time.append(avg_time)
                        times.append(time.time() - start_t)

                times_list.append(sum(times)/len(times))
                times_sd_list.append(statistics.stdev(times))
                moves_list.append(sum(number_of_moves)/len(number_of_moves))
                moves_sd_list.append(statistics.stdev(number_of_moves))
            file.write("@"*10 + f"{rule}" + "@"*10 + "\n")
            file.write(f"moves: {moves_list}\n")
            file.write(f"moves_sd: {moves_sd_list}\n")
            file.write(f"times: {times_list}\n")
            file.write(f"times_sd: {times_sd_list}\n")
            file.flush()

    file.close()


def run_experiments():
    args_low = {
        "C": 1.4,  # srqt 2
        "num_searches": 200,  # Budget per rollout
        "num_simulations": 1,  # Budget for extra simulations per node
        "attempt": 0,
    }
    args_high = {
        "C": 1.4,  # srqt 2
        "num_searches": 800,  # Budget per rollout
        "num_simulations": 1,  # Budget for extra simulations per node
        "attempt": 0,
    }
    env = trueskill.TrueSkill()
    empty_attempts_folder()
    args = get_argument_parser_args()

    # p1 = players.random_bot()
    # p2 = players.random_bot()
    # p1 = players.heuristic_bot()
    # p2 = players.heuristic_bot()
    # p1 = players.human_player()
    # p2 = players.human_player()
    agent_wincount = {"random": 0, "heuristic": 0, "low_mcts": 0, "high_mcts": 0}
    agent_map = {
        "random": players.random_bot,
        "heuristic": players.heuristic_bot,
        "human": players.human_player,
        "low_mcts": None,
        "high_mcts": None,
    }
    if args.num_columns % 2 == 1 and args.num_rows % 2 == 0:
        warning_len = len(
            "# WARNING: If the number of columns is uneven and the number of rows is even the board is not symmetrical. #"
        )
        print("#" * warning_len)
        print(
            "# WARNING: If the number of columns is uneven and the number of rows is even the board is not symmetrical. #\n# To assure an equal number of pieces, set the number of vertical pieces to an even value.                 #"
        )
        print("#" * warning_len)
        time.sleep(5)
    file = open("./results2.txt", "w")
    file.close()
    file = open("./results2.txt", "a")
    rules = [CheckersRules.QUANTUM_V2]
    # rules = [CheckersRules.QUANTUM_V2]
    sizes = [12, 14]
    # agents = ["random", "heuristic", "low_mcts", "high_mcts"]
    # just mcts agents
    agents = ["random", "random"]
    for rule in rules:
        for size in sizes:
            # ratings = {
            #     'random': trueskill.Rating(mu=16.947, sigma=2.045),
            #     'heuristic': trueskill.Rating(mu=22.949, sigma=1.638),
            #     'low_mcts': trueskill.Rating(mu=29.595, sigma=1.681),
            #     'high_mcts': trueskill.Rating(mu=30.348, sigma=1.654)
            # }
            # default ratings
            ratings = {
                "random": trueskill.Rating(),
                "heuristic": trueskill.Rating(),
                "low_mcts": trueskill.Rating(),
                "high_mcts": trueskill.Rating(),
            }
            # size = 5
            # rule = CheckersRules.CLASSICAL
            times = []
            results = []
            number_of_moves = []
            avg_mcts_time = []
            movetypes = {"CLASSIC": 0, "SPLIT": 0, "ENTANGLE": 0, "TAKE": 0}
            file.write("@" * 200 + "\n")
            file.write(f"Rule: {rule}\n")
            file.write(f"Board size: {size}x{size}\n")
            file.write("@" * 200 + "\n")
            print(f"Board size: {size}x{size}, Rule: {rule}")
            iterations = args.iterations
            low_white_wins = 0
            high_white_wins = 0
            low_black_wins = 0
            high_black_wins = 0
            low_wins = 0
            high_wins = 0
            for k in range(iterations):
                if k % 250 == 0 and k != 0:
                    print(
                        f"Iteration: {k+1} at {time.strftime('%H:%M', time.localtime())}"
                    )
                sd = random.randint(0, 100000000000000000)
                # sd = 4271756581358815
                random.seed(sd)
                random.shuffle(agents)
                matches = generate_matches(agents)
                # print("Matches:", matches)
                for i, j in matches:
                    white_mcts = False
                    black_mcts = False
                    args1 = None
                    args2 = None
                    p1 = None
                    p2 = None

                    if i == "random" or i == "heuristic" or i == "human":
                        p1 = agent_map[i]()
                    if j == "random" or j == "heuristic" or j == "human":
                        p2 = agent_map[j]()
                    if i == "low_mcts":
                        args1 = args_low
                        white_mcts = True
                    elif i == "high_mcts":
                        args1 = args_high
                        white_mcts = True

                    if j == "low_mcts":
                        args2 = args_low
                        black_mcts = True
                    elif j == "high_mcts":
                        args2 = args_high
                        black_mcts = True
                    args_low["attempt"] = k
                    args_high["attempt"] = k
                    seed_str = f"Seed: {sd}\n"
                    # write_attempt(k, seed_str)
                    start_t = time.time()
                    checkers = Checkers(
                        num_vertical=size,
                        num_horizontal=size,
                        num_vertical_pieces=args.num_vertical_pieces,
                        SIMULATE_QUANTUM=args.sim_q,
                        rules=rule,
                    )
                    game = GameInterface(
                        checkers,
                        white_player=p1,
                        black_player=p2,
                        GUI=(not args.disable_GUI),
                        white_mcts=white_mcts,
                        black_mcts=black_mcts,
                        args_1=args1,
                        args_2=args2,
                        print=False,
                        attempt=k,
                    )
                    result, num_moves, avg_time, single_movetypes = game.play()
                    results.append(result)
                    if result == CheckersResult.WHITE_WINS:
                        new_r1, new_r2 = env.rate_1vs1(ratings[i], ratings[j])
                        agent_wincount[i] += 1
                        if i == "low_mcts":
                            low_wins += 1
                            low_white_wins += 1
                        elif i == "high_mcts":
                            high_white_wins += 1
                            high_wins += 1
                    elif result == CheckersResult.BLACK_WINS:
                        agent_wincount[j] += 1
                        if j == "low_mcts":
                            low_wins += 1
                            low_black_wins += 1
                        elif j == "high_mcts":
                            high_wins += 1
                            high_black_wins += 1
                        new_r2, new_r1 = env.rate_1vs1(ratings[j], ratings[i])
                    else:  # draw
                        new_r1, new_r2 = env.rate_1vs1(
                            ratings[i], ratings[j], drawn=True
                        )

                    ratings[i] = new_r1
                    ratings[j] = new_r2
                    number_of_moves.append(num_moves)
                    avg_mcts_time.append(avg_time)
                    times.append(time.time() - start_t)
                    for l in movetypes:
                        movetypes[l] += single_movetypes[l]
            file.write("iteration: " + str(k) + "\n")
            file.write(f"All times: {times}\n")
            file.write(f"All moves: {number_of_moves}\n")
            # file.write(f"White agent: {i}, Black agent: {j}\n")
            file.write(
                f"Average time: {sum(times)/len(times)}, minimum time: {min(times)}, max time: {max(times)}\n"
            )
            file.write(f"Standard deviation average times: {statistics.stdev(times)}\n")
            file.write(
                f"Average number of moves: {sum(number_of_moves)/len(number_of_moves)}\n"
            )
            file.write(
                f"Standard deviation average number of moves: {statistics.stdev(number_of_moves)}\n"
            )
            file.write(
                f"Draw: {results.count(CheckersResult.DRAW)}, White wins: {results.count(CheckersResult.WHITE_WINS)}, Black wins: {results.count(CheckersResult.BLACK_WINS)}\n"
            )

    file.close()


def play_normal_game(args):
    args_low = {
        "C": 1.4,  # srqt 2
        "num_searches": 200,  # Budget per rollout
        "num_simulations": 1,  # Budget for extra simulations per node
        "attempt": 0,
    }
    args_high = {
        "C": 1.4,  # srqt 2
        "num_searches": 800,  # Budget per rollout
        "num_simulations": 1,  # Budget for extra simulations per node
        "attempt": 0,
    }

    env = trueskill.TrueSkill()
    empty_attempts_folder()
    white_mcts = False
    black_mcts = False
    args1 = args_high
    args2 = args_high

    agent_wincount = {"random": 0, "heuristic": 0, "low_mcts": 0, "high_mcts": 0}
    agent_map = {
        "random": players.random_bot,
        "heuristic": players.heuristic_bot,
        "human": players.human_player,
        "low_mcts": None,
        "high_mcts": None,
    }
    p1 = agent_map[args.p1]()
    p2 = agent_map[args.p2]()

    quantum_rule_map = {
        "classical": CheckersRules.CLASSICAL,
        "superposition": CheckersRules.QUANTUM_V1,
        "entanglement": CheckersRules.QUANTUM_V2
    }
    rule = quantum_rule_map[args.rule_set]
    
    if args.num_columns % 2 == 1 and args.num_rows % 2 == 0:
        warning_len = len(
            "# WARNING: If the number of columns is uneven and the number of rows is even the board is not symmetrical. #"
        )
        print("#" * warning_len)
        print(
            "# WARNING: If the number of columns is uneven and the number of rows is even the board is not symmetrical. #\n# To assure an equal number of pieces, set the number of vertical pieces to an even value.                 #"
        )
        print("#" * warning_len)
        time.sleep(5)

    checkers = Checkers(
        num_vertical=args.num_rows,
        num_horizontal=args.num_columns,
        num_vertical_pieces=args.num_vertical_pieces,
        SIMULATE_QUANTUM=args.sim_q,
        rules=rule,
    )
    game = GameInterface(
        checkers,
        white_player=p1,
        black_player=p2,
        GUI=not args.disable_GUI,
        white_mcts=white_mcts,
        black_mcts=black_mcts,
        args_1=args1,
        args_2=args2,
        print=True,
        attempt=99999999,
    )
    result, num_moves, avg_time, single_movetypes = game.play()
    if result == CheckersResult.WHITE_WINS:
        print("White wins!")
    elif result == CheckersResult.BLACK_WINS:
        print("Black wins!")
    else:
        print("Draw!")


def main():
    args = get_argument_parser_args()

    if args.do_average_moves_and_time_experiment:
        run_average_moves_and_times_experiment(args)
        exit()

    # run_experiments()
    play_normal_game(args)


if __name__ == "__main__":
    main()

# Generate prof:  python3 -m cProfile -o main.prof main.py
# Visualise prof: snakeviz main.prof

# EXPERIMENT TO DO:
# REDO experiments for average number of moves and time per game for different board sizes
# Save all the data values for each game (e.g. time for one game and number of moves for one game)
# Make a graph and for each board size:
# calculate average number of moves/time
# calculate standard deviation
