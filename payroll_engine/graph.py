"""Dependency Graph: nodos `rule:<rule_id>` y `base:<CODIGO>`. Detecta ciclos,
dependencias faltantes y produce un orden de ejecución determinista (desempate
por identificador) para que el cálculo y su traza sean reproducibles."""

import heapq

from .conditions import referenced_bases, referenced_lines
from .errors import CycleError, MissingDependencyError
from .mechanisms import mechanism_bases


class DependencyGraph:
    def __init__(self):
        self.nodes = {}       # id -> {"type": "rule"|"base", "ref": obj}
        self.edges = {}       # id -> set(ids de los que depende)

    def add_node(self, node_id, kind, ref):
        self.nodes[node_id] = {"type": kind, "ref": ref}
        self.edges.setdefault(node_id, set())

    def add_edge(self, node_id, depends_on):
        if depends_on not in self.nodes:
            raise MissingDependencyError(f"{node_id} depende de {depends_on}, que no existe en el grafo")
        self.edges[node_id].add(depends_on)

    def order(self):
        """Orden topológico determinista (Kahn con desempate lexicográfico)."""
        remaining = {n: set(deps) for n, deps in self.edges.items()}
        dependents = {n: set() for n in remaining}
        for node, deps in remaining.items():
            for dep in deps:
                dependents[dep].add(node)
        ready = [n for n, deps in remaining.items() if not deps]
        heapq.heapify(ready)
        ordered = []
        while ready:
            node = heapq.heappop(ready)
            ordered.append(node)
            for nxt in sorted(dependents[node]):
                remaining[nxt].discard(node)
                if not remaining[nxt] and nxt not in ordered and nxt not in ready:
                    heapq.heappush(ready, nxt)
        if len(ordered) != len(remaining):
            cycle = self._find_cycle({n: d for n, d in remaining.items() if n not in ordered})
            raise CycleError("ciclo en el grafo de dependencias", details=[" -> ".join(cycle)])
        return ordered

    @staticmethod
    def _find_cycle(pending):
        node = sorted(pending)[0]
        path, seen = [], {}
        while node not in seen:
            seen[node] = len(path)
            path.append(node)
            deps = sorted(d for d in pending.get(node, ()) if d in pending)
            if not deps:
                break
            node = deps[0]
        return path[seen.get(node, 0):] + [node]


def build_graph(selected, base_defs, concepts):
    """selected: SelectedRule (una o más versiones por segmento). base_defs: bases vigentes por
    código. concepts: dict concepto -> definición. Devuelve el grafo con todas las aristas."""
    graph = DependencyGraph()
    producers = {}                                   # concepto -> [node ids]
    for sel in selected:
        node_id = f"rule:{sel.node_key}"
        graph.add_node(node_id, "rule", sel)
        if sel.kind != "VALIDATION":
            producers.setdefault(sel.concept, []).append(node_id)
    for code, base in base_defs.items():
        graph.add_node(f"base:{code}", "base", base)

    # una base depende de las reglas cuyo concepto tiene un tratamiento hacia ella
    for code, base in base_defs.items():
        node = f"base:{code}"
        for concept_code, concept in concepts.items():
            if any(tr["base"] == code for tr in concept.get("treatments", [])):
                for producer in producers.get(concept_code, []):
                    graph.add_edge(node, producer)
        for concept_code in base.get("subtract_lines", []):
            producers_of = producers.get(concept_code)
            if not producers_of:
                raise MissingDependencyError(f"la base {code} resta el concepto {concept_code}, que ninguna regla produce")
            for producer in producers_of:
                graph.add_edge(node, producer)

    # una regla depende de las bases y líneas que lee (en cualquiera de sus versiones)
    for sel in selected:
        node = f"rule:{sel.node_key}"
        for rule in sel.versions():
            params = rule.get("calculation", {}).get("params", {})
            needed_bases = mechanism_bases(params) | referenced_bases(rule.get("conditions"))                 | referenced_bases(rule.get("exceptions", []))
            for code in sorted(needed_bases):
                if code not in base_defs:
                    raise MissingDependencyError(f"{rule['rule_id']} usa la base {code}, que no está vigente/definida")
                graph.add_edge(node, f"base:{code}")
            needed_lines = referenced_lines(params) | referenced_lines(rule.get("conditions"))                 | referenced_lines(rule.get("exceptions", []))
            for concept_code in sorted(needed_lines):
                producers_of = producers.get(concept_code)
                if not producers_of:
                    raise MissingDependencyError(f"{rule['rule_id']} usa la línea {concept_code}, que ninguna regla produce")
                for producer in producers_of:
                    if producer != node:
                        graph.add_edge(node, producer)
    return graph
