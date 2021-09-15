Messages (from the train)
=========================

The intelino train sends a lot of valuable information which is accessible
through typed data classes (read only). Some of this information comes as
events and some are delivered as responses to single requests or stream
requests.

Base classes
------------

Base classes are not intended for use, but it is good to know what have
all messages in common.

.. autoclass:: trainlib_async.messages.TrainMsgBase()
   :members:
   :inherited-members:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventBase()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventSensorColorChangedBase()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

Response messages
-----------------

.. autoclass:: trainlib_async.messages.TrainMsgMacAddress()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgTrainUuid()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgVersionDetail()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgStatsLifetimeOdometer()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgMovement()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

Event messages
--------------

.. autoclass:: trainlib_async.messages.TrainMsgEventMovementDirectionChanged()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventLowBattery()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventChargingStateChanged()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventButtonPressDetected()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventSnapCommandDetected()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventSnapCommandExecuted()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventFrontColorChanged()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventBackColorChanged()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventSplitDecision()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource


Error messages
--------------

.. autoclass:: trainlib_async.messages.TrainMsgUnknown()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventUnknown()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgMalformed()
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource

Union classes
-------------

The library defines aliased union classes for messages. These should be used
instead of the base classes e.g. when a function expects various message types
as arguments.

.. autoclass:: trainlib_async.messages.TrainMsg
   :members:
   :inherited-members:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEvent
   :members:
   :inherited-members:
   :member-order: bysource

.. autoclass:: trainlib_async.messages.TrainMsgEventSensorColorChanged
   :members:
   :inherited-members:
   :member-order: bysource
