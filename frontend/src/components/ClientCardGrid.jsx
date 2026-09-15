import ClientCard from "./ClientCard.jsx";

// Renders one card per client (Dashboard Spec Ch.7.1). Uses an
// auto-filling grid so this reads correctly whether there are 5, 10,
// or 20 clients (Phase 04 acceptance criteria).
export default function ClientCardGrid({ partition }) {
  return (
    <section aria-labelledby="client-cards-heading">
      <h2 id="client-cards-heading">Client Cards</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {partition.clients.map((client) => (
          <ClientCard key={client.client_id} client={client} strategy={partition.strategy} />
        ))}
      </div>
    </section>
  );
}
