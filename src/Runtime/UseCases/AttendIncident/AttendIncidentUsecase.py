from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.Adapters.RuntimeResponseAdapter import RuntimeResponseAdapter
from Runtime.Internals.Executors.EasyAgentResult import EasyAgentResult
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort


class AttendIncidentUsecase:
    def __init__(self, graph: IRuntimeGraphPort) -> None:
        self._graph = graph

    async def execute_async(self, request: RuntimeRequestAdapter) -> EasyAgentResult[RuntimeResponseAdapter]:
        graph_input = request.to_graph_input()
        state = await self._graph.ainvoke(graph_input, {"configurable": {"thread_id": request.thread_id}})
        return EasyAgentResult.success(RuntimeResponseAdapter.from_graph_state(state, request.thread_id, request.correlation_id))
