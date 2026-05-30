import { getAuditEvents } from "../lib/platform-api";

export default async function AdminPage() {
  const auditEvents = await getAuditEvents();

  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>Admin console</h2>
          <p>
            Centralize user management, role assignment, access history, audit
            events and tenant configuration.
          </p>
        </div>
      </section>
      <section className="panel">
        <h3>Recent audit events</h3>
        {auditEvents.length === 0 ? (
          <p className="muted">No audit events are available.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Actor</th>
                <th>Correlation</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map((event) => (
                <tr key={event.id}>
                  <td>{event.created_at}</td>
                  <td>{event.action}</td>
                  <td>{event.resource_type} / {event.resource_id}</td>
                  <td>{event.actor_user_id || "system"}</td>
                  <td>{event.correlation_id || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
