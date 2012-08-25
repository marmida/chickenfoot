'web application that serves chickenfoot API calls'

from __future__ import absolute_import

import flask
import json
import optparse
import random

# create app as a module variable so we can use decorators for routes
app = flask.Flask('chickenfoot')

@app.route("/game/<game_id>")
def hello(game_id):
	# we should always generate the same game results, so long as the simulation code hasn't changed
	random.seed(game_id)

	response = flask.make_response(json.dumps({
    	'tableau': [
    		{'a': 9, 'b': 9, 'turn': 1, 'inverted': False},
        	{'a': 9, 'b': 1, 'turn': 2, 'inverted': False},
        	{'a': 9, 'b': 4, 'turn': 3, 'inverted': False},
        	[
        		{'a': 9, 'b': 2, 'turn': 4, 'inverted': False},
				[
	                {'a': 2, 'b': 2, 'turn': 7, 'inverted': False},
	                {'a': 4, 'b': 2, 'turn': 6, 'inverted': True},
	                {'a': 2, 'b': 1, 'turn': 5, 'inverted': False},
	            ],
        	],
        ],	
	}))
	response.headers['Access-Control-Allow-Origin'] = '*' # todo: maybe this should be handled by nginx proxy up front?
	return response

def parse_args():
	parser = optparse.OptionParser(
		description='Launch the chickenfoot simulation API server',
	)
	parser.add_option('-g', '--debug', help='Enable debugging', action='store_true', default=False)
	parser.add_option('-p', '--port', help='Specify the port on which to listen for connections',
		action='store', default=10001)
	parser.add_option('-i', '--interface', help='Specify the interface on which to listen for connections',
		action='store')
	return parser.parse_args()

def main():
	opts, args = parse_args()
	app.run(debug=opts.debug, host=opts.interface, port=opts.port)

if __name__ == "__main__":
    main()