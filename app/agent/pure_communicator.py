import queue
import threading
import time


def agent_chat_generator(agent, message, session_id):
    """agent reply generator"""
    reply_queue = queue.Queue()
    agent.active_session(session_id)

    @agent.on_event("delta")
    def on_delta(data):
        reply_queue.put_nowait(data)

    @agent.on_event("done")
    def on_done(data):
        reply_queue.put_nowait("$STOP")

    agent_thread = threading.Thread(target=agent.input(message).start)
    agent_thread.start()
    while True:
        reply = reply_queue.get()
        if reply == "$STOP":
            break
        for r in list(reply):
            time.sleep(0.02)
            yield r
    agent_thread.join()
    agent.stop_session()


from .talent_center import center


class PureCommunicator:
    def __init__(self):
        self.agent = center.create_agent(agent_id="pure_communicator")

    def chat(self, message, session_id="1"):
        return agent_chat_generator(self.agent, message, session_id)
