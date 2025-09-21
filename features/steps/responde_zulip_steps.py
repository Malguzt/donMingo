
from behave import given, when, then
from behave.api.pending_step import StepNotImplementedError

@given(u'the Zulip API is accessible')
def step_impl(context):
    raise StepNotImplementedError(u'Given the Zulip API is accessible')

@given(u'the mocked Zulip server is running')
def step_impl(context):
    raise StepNotImplementedError(u'Given the mocked Zulip server is running')

@given(u'the mocked responses a list of 3 unread topic')
def step_impl(context):
    raise StepNotImplementedError(u'Given the mocked responses a list of 3 unread topic')

@when(u'the system processes each unread topic')
def step_impl(context):
    raise StepNotImplementedError(u'When the system processes each unread topic')

@then(u'it should send a response to each topic')
def step_impl(context):
    raise StepNotImplementedError(u'Then it should send a response to each topic')

@when(u'the system marks topics as read')
def step_impl(context):
    raise StepNotImplementedError(u'When the system marks topics as read')

@then(u'it should confirm that all topics are marked as read')
def step_impl(context):
    raise StepNotImplementedError(u'Then it should confirm that all topics are marked as read')
