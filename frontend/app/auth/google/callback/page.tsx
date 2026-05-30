import { GoogleCallbackForm } from "./google-callback-form";

export default function GoogleCallbackPage() {
  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <p className="eyebrow">Authentication</p>
          <h2>Google SSO callback</h2>
          <p>
            Complete the Google sign-in exchange and store the tenant-scoped
            platform session.
          </p>
        </div>
      </section>
      <GoogleCallbackForm />
    </div>
  );
}
