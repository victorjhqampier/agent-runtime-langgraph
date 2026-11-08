from Runtime.Adapters.RuntimeRequestAdapter import RuntimeRequestAdapter
from Runtime.Adapters.RuntimeResponseAdapter import RuntimeResponseAdapter
from Runtime.Internals.Executors.EasyAgentResult import EasyAgentResult
from Runtime.Ports.IRuntimeGraphPort import IRuntimeGraphPort


class AttendIncidentUsecase:
    """Punto de entrada y salida del caso de uso `attend_incident`.

    Recibe un `RuntimeRequestAdapter` ya validado por Presentation, lo traduce a entrada
    del grafo LangGraph, invoca el puerto `IRuntimeGraphPort` y devuelve un
    `EasyAgentResult[RuntimeResponseAdapter]` con estados semánticos
    (resolved, needs_clarification, escalated, failed, rejected). No contiene lógica de negocio
    ni conoce implementaciones de Infrastructure.
    """

    def __init__(self, graph: IRuntimeGraphPort) -> None:
        self._graph = graph

    async def execute_async(self, request: RuntimeRequestAdapter) -> EasyAgentResult[RuntimeResponseAdapter]:
        """Ejecuta el caso de uso atendiendo un incidente.

        Convierte el request en entrada del grafo, invoca el workflow con el `thread_id`
        del request (para checkpointer duradero y reanudación) y mapea el estado final
        a `RuntimeResponseAdapter`.
        """
        graph_input = request.to_graph_input()
        state = await self._graph.ainvoke(graph_input, {"configurable": {"thread_id": request.thread_id}})
        return EasyAgentResult.success(RuntimeResponseAdapter.from_graph_state(state, request.thread_id, request.correlation_id))
