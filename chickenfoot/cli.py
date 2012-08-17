'''
Command-line interface for interacting with the simulation
'''
from __future__ import absolute_import

import itertools
import optparse

import chickenfoot.game

class GameRunner(object):
	def __init__(self, rounds, player_class_names, set_size, starting_hand_size, reporter_class_names):
		self.rounds = rounds
		self.players = [getattr(chickenfoot.game, class_name)('p%d' % num) for num, class_name in enumerate(player_class_names)]
		self.set_size = set_size
		self.starting_hand_size = starting_hand_size
		self.reporters = [getattr(chickenfoot.game, class_name)() for class_name in reporter_class_names]
		self.aggregate_scores = dict((player, 0) for player in self.players)

	def run(self):
		required_root_iterator = itertools.cycle(xrange(self.set_size+1))
		for i in xrange(self.rounds):
			# FIXME: kind of funky to require .next()
			required_root = required_root_iterator.next()
			game = chickenfoot.game.Game(required_root, self.set_size, self.starting_hand_size, self.players, reporters=self.reporters)
			game.run()
			for player in self.players:
				self.aggregate_scores[player] += game.scores[player]

def validate_positive_int(s, name, error_method):
	'''
	Returns the string s as an int.

	If the int value of s is either invalid or less than 1, call error_method with a description.
	This is most useful when provided the 'error' method of an optparse.OptionParser instance.
	'''
	# test converting s to an int
	try: 
		num = int(s)
	except ValueError:
		error_method('Invalid %s: %s; must be a number' % (name, s))
	
	# guarantee num > 0
	if num <= 0:
		error_method('Invalid %s: %s; must be greater than 0' % (name, num))

	return num

def parse_args():
	'''
	Evaluates the invoking command line and returns (opts, num_rounds), wherein 'opts'
	is in the style of optparse.OptionParser.


	Exits via OptionParser.error if the command line is invalid (e.g. bad options or args).
	'''
	parser = optparse.OptionParser(
		usage='%prog N',
		description='Simulates running N number of rounds of the dominoes game, "Chicken foot," and prints a result summary',
	)
	parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=False)
	parser.add_option('-p', '--player', action='append', dest='players', default=[],
		help='Class names from which to create Player instances; can be repeated to provide multiple players. '
				'Defaults to two players: a MaxValuePlayer and a RandomPlayer. '
				'Because this program currently doesn\'t allow loading external code, '
				'this option isn\'t all that useful.')
	parser.add_option('--set-size', action='store', dest='set_size', default=9,
		help='Domino set size, given as the "double X" set size; e.g. "9" for a "double nine" set.  Default: 9')
	parser.add_option('--starting-hand-size', action='store', dest='starting_hand_size', default=7,
		help='Number of tiles that each player begins with in their hand.  Default: 7')

	opts, args = parser.parse_args()
	
	# odd: optparse treats the default for 'append' options differently - it does not override them with
	# whatever is provided by the user on the command line.
	# see http://bugs.python.org/issue5088
	# we'll manually assign a default
	if not opts.players:
		opts.players = ['MaxValuePlayer', 'RandomPlayer']
	
	if len(args) != 1:
		parser.error('Requires a number of a rounds to simulate.')
	
	num_rounds = validate_positive_int(args[0], 'number of rounds', parser.error)
	
	# validate player class names
	for class_name in opts.players:
		player_class = getattr(chickenfoot.game, class_name, False)
		if not player_class:
			parser.error('Invalid player class: %s' % class_name)
		# we'll assume that if the class has '_pick_tile', then it's a Player derivative
		if not hasattr(player_class, '_pick_tile'):
			parser.error('Invalid player class: %s' % class_name)

	# validate numeric args
	opts.set_size = validate_positive_int(opts.set_size, 'set size', parser.error)
	opts.starting_hand_size = validate_positive_int(opts.starting_hand_size, 'starting hand size', parser.error)

	return (opts, num_rounds)

def main():
	'''
	Runs the simulation.

	Create a GameRunner, seed it with options parsed from the command line, and invoke it.
	'''
	opts, num_rounds = parse_args()

	# figure out what we'll report to
	reporters = ['LoggingReporter'] if opts.verbose else []

	# build the runner, start a timer, and away we go
	runner = GameRunner(num_rounds, opts.players, opts.set_size, opts.starting_hand_size, reporters)
	start_time = time.time()
	runner.run()
	end_time = time.time()

	print 'Rounds:       %d' % runner.rounds
	print 'Time elapsed: %.3f secs' % (end_time - start_time)
	print 'Rounds/sec:   %.3f' % (float(runner.rounds) / (end_time - start_time))
	print ''
	print 'Aggregate scores:'
	for player, score in runner.aggregate_scores.iteritems():
		print '%35s % 10d' % (player, score)

if __name__ == '__main__':
	main()