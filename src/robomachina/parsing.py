#  Copyright 2011-2012 Mikko Korpela
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from pyparsing import *
from robomachina.model import RoboMachina, State, Action, Variable

state_name = Regex(r'\w+( \w+)*')
state_name.leaveWhitespace()
state_name.setParseAction(lambda t: ''.join(t))
state_name = state_name.setResultsName('state_name')

robo_step = Regex(r'([\w\$\{\}][ \w\$\{\}]*[\w\}]|\w)')
robo_step.leaveWhitespace()
robo_step = robo_step.setResultsName('robo_step')

variable = Regex(r'\$\{[_A-Z][_A-Z0-9]*\}')

variable_value = Word(alphanums+'${}')+ZeroOrMore(' '+Word(alphanums+'${}'))

variable_values = (variable_value+ZeroOrMore('  '+variable_value)).setResultsName('variable_values')
variable_values.setParseAction(lambda t: [[t[2*i] for i in range((len(t)+1)/2)]])

variable_definition = variable.setResultsName('variable_name') + '  any of  ' + variable_values + LineEnd()
variable_definition.leaveWhitespace()
variable_definition.setParseAction(lambda t: [Variable(t.variable_name, list(t.variable_values))])

step = White(min=2)+robo_step+LineEnd()
step.leaveWhitespace()
step.setParseAction(lambda t: ['  '+t.robo_step])

action_header = White(min=2)+'[Actions]'
condition = Regex('((  when  [\${}\w]+ == \w+( and [\${}\w]+ == \w+)*)|  otherwise)?')
def parse_condition(cond):
    if not cond[0]:
        return cond
    if cond[0].startswith('  when  '):
        return [cond[0][8:]]
    return ['otherwise']

condition.setParseAction(parse_condition)
condition = condition.setResultsName('condition')
action = White(min=4)+robo_step + White(min=2) + '==>'+White(min=2) + state_name + condition + LineEnd()
action.leaveWhitespace()
action.setParseAction(lambda t: [Action(t.robo_step.rstrip(), t.state_name, t.condition)])

actions = action_header + LineEnd() + OneOrMore(action).setResultsName('actions')
actions = Optional(actions)
actions.leaveWhitespace()
actions.setResultsName('actions')

steps = ZeroOrMore(step).setResultsName('steps')

state = state_name + LineEnd() + steps + actions
state.leaveWhitespace()
state.setParseAction(lambda p: State(p.state_name, list(p.steps), list(p.actions)))

machina_header = Literal('*** Machine ***')+LineEnd()
states = state+ZeroOrMore(LineEnd()+state)
states.setParseAction(lambda t: [[t[2*i] for i in range((len(t)+1)/2)]])
states = states.setResultsName('states')
variables = ZeroOrMore(variable_definition).setResultsName('variables')
machina = machina_header+variables+states
machina.setParseAction(lambda p: RoboMachina(list(p.states), list(p.variables)))
machina.setWhitespaceChars(' ')

def parse(text):
    return machina.parseString(text, parseAll=True)[0]
