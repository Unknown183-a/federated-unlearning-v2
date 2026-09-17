import ClientCard from "./ClientCard.jsx";

// Renders one card per client (Dashboard Spec Ch.7.1). Uses an
// auto-filling grid so this reads correctly whether there are 5, 10,
// or 20 clients (Phase 04 acceptance criteria).
export default function ClientCardGrid({ partition, selectable, selectedClientId, onSelect, heading = "Client Cards" }) {
  return (
    <section aria-labelledby="client-cards-heading">
      <h2 id="client-cards-heading" className="text-base font-semibold text-gray-900">
        {heading}
      </h2>
      <div className="mt-4 grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(180px,1fr))]">
        {partition.clients.map((client) => (
          <ClientCard
            key={client.client_id}
            client={client}
            strategy={partition.strategy}
            selectable={selectable}
            selected={selectable && client.client_id === selectedClientId}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}
