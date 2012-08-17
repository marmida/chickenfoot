'tests for cli.py'

from __future__ import absolute_import

import optparse
import unittest

import chickenfoot.cli
from chickenfoot.tests.util import MockContext

class ParseArgsTest(unittest.TestCase):
	class MockExit(Exception):
		pass

	class MockOptionParser(object):
		'''
		A mock for optparse.OptionParser.  Calling its "parse_args" method returns a canned
		response.  Raises MockExit when its "error" method is called.
		'''

		def __init__(self, opts, args):
			'Store opts and args so they can be returned by parse_args'
			self.opts = opts
			self.args = args
		
		def __call__(self, *args, **kwargs):
			'''
			Funky: we're going to mock the *class* optparse.OptionParser with *instances* of this class.
			Thus, they will be called like this:
				parser = optparse.OptionParser(...)
			
			Because we this instance is already suitable for substitution for OptionParser instances,
			we implement __call__ to return self.
			'''
			return self

		def add_option(self, *args, **kwargs):
			'no-op'
			pass

		def parse_args(self):
			'Return whatever we were primed to return'
			return (self.opts, self.args)

		def error(self, message):
			'''
			Instead of actually exiting, we\'ll raise an exception that will be caught by MockOptionContext.
			That way, the calling function will be exited, but the whole application won't attempt to quit.
			'''
			raise ParseArgsTest.MockExit(message)

	class MockParserContext(object):
		'a context manager for use with MockOptionParser'
		def __init__(self, test_case=None, expected_error=None):
			self.test_case = test_case
			self.expected_error = expected_error
			
		def __enter__(self):
			return self

		def __exit__(self, exc_type, exc_val, tb):
			if exc_type == ParseArgsTest.MockExit:
				if not self.expected_error:
					# OptionParser.error was called, although we didn't expect that
					self.test_case.fail('Unexpected call to OptionParser.error with message: %s' % exc_val.args[0])
				
				# assert that the error message is what we expect
				self.test_case.assertEquals(self.expected_error, exc_val.args[0])

				# everything is hunky dory, suppress this exception
				return True
			
			elif not exc_type and self.expected_error:
				# we are exiting the context without hitting an expected exception; that's a problem
				self.test_case.fail('Did not call OptionParser.error as required')

			# if exc_type is True, we're handling an unexpected exception, and should let it pass through

	class MockValues(object):
		'Mocks optparse.Values'
		def __init__(self, attrs):
			'set attributes named after the keys in "attrs", with corresponding values'
			if 'players' not in attrs:
				attrs['players'] = []
			for attrname, attrval in attrs.iteritems():
				setattr(self, attrname, attrval)

	def _execute(self, opt_attrs, args, expected_error=None):
		# build the "opts" object (ala optparse.Values) from the provided mapping object
		with self.MockParserContext(self, expected_error) as context:
			with MockContext(optparse, 'OptionParser', self.MockOptionParser(self.MockValues(opt_attrs), args)):
				return chickenfoot.cli.parse_args()

	def test_no_args(self):
		'parse_args: exits with a message when no args are provided'
		self._execute({}, [], expected_error='Requires a number of a rounds to simulate.')

	def test_non_numeric_num_rounds(self):
		'parse_args: complains when it gets a non-numeric number of rounds'
		self._execute({}, ['a'], expected_error='Invalid number of rounds: a; must be a number')

	def test_invalid_num_rounds(self):
		'parse_args: complains when number of rounds is negative or zero'
		self._execute({}, ['-1'], expected_error='Invalid number of rounds: -1; must be greater than 0')
		self._execute({}, ['0'], expected_error='Invalid number of rounds: 0; must be greater than 0')

	def test_option_validation(self):
		'parse_args: validates the player, set size, and starting hand size options'
		default_opts = {
			'players': ['MaxValuePlayer', 'RandomPlayer'],
			'set_size': 9,
			'starting_hand_size': 7,
		}

		opts = default_opts.copy()
		opts['players'] = ['MaxValuePlayer', 'not a player class']
		self._execute(opts, ['1'], expected_error='Invalid player class: not a player class')

		opts = default_opts.copy()
		opts['players'] = ['MaxValuePlayer', 'Game']
		self._execute(opts, ['1'], expected_error='Invalid player class: Game')

		opts = default_opts.copy()
		opts['set_size'] = 'a'
		self._execute(opts, ['1'], expected_error='Invalid set size: a; must be a number')
		
		opts = default_opts.copy()
		opts['starting_hand_size'] = 'a'
		self._execute(opts, ['1'], expected_error='Invalid starting hand size: a; must be a number')
		
		# valid case
		actual, args = self._execute(default_opts, ['1'])
		self.assertEquals(['MaxValuePlayer', 'RandomPlayer'], actual.players)
		self.assertEquals(9, actual.set_size)
		self.assertEquals(7, actual.starting_hand_size)



class GameRunnerTest(unittest.TestCase):
	def test_run(self):
		'GameRunner.run: creates Games and calls their "run" methods'
		# binding for lookup inside MockGame.__init__
		executing_test = self

		class MockGame(object):
			'Mocks chickenfoot.cli.Game'
			# track how many instances are created
			instance_count = 0

			def __init__(self, required_root, set_size, starting_hand_size, players, reporters):
				'assert that args provided are as expected'
				# todo: assert required_root - how?
				executing_test.assertEquals(2, set_size)
				executing_test.assertEquals(3, starting_hand_size)
				# player properties
				executing_test.assertEquals(
					[
						chickenfoot.game.MaxValuePlayer, 
						chickenfoot.game.RandomPlayer, 
						chickenfoot.game.MaxValuePlayer, 
						chickenfoot.game.RandomPlayer
					], 
					[i.__class__ for i in players]
				)
				executing_test.assertEquals(['p0', 'p1', 'p2', 'p3'], [i.name for i in players])
				# reporters
				executing_test.assertEquals([chickenfoot.game.LoggingReporter], [i.__class__ for i in reporters])

				# must copy in players for interaction with GameRunner.aggregate_scores
				self.players = players
				# increment the count
				self.__class__.instance_count += 1

			def run(self):
				'Generate bogus, predictable scores'
				self.scores = dict((player, i*5) for i, player in enumerate(self.players))

		runner = chickenfoot.cli.GameRunner(10, ['MaxValuePlayer', 'RandomPlayer', 'MaxValuePlayer', 'RandomPlayer'], 2, 3, ['LoggingReporter'])
		with MockContext(chickenfoot.game, 'Game', MockGame):
			runner.run()
		
		# one game should have been created per round
		self.assertEquals(10, MockGame.instance_count)
		# aggregate scores should be 10 * each round, which is (p1: 0, p2: 5, p3: 10, p4: 15)
		expected = {
			'p0': 0,
			'p1': 50,
			'p2': 100,
			'p3': 150,
		}
		self.assertEquals(expected, dict([(player.name, score) for player, score in runner.aggregate_scores.iteritems()]))
