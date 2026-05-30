"use client";

import { FormEvent, useState } from "react";

import { apiPost, storeAccessToken } from "../../../lib/api-client";

type CallbackState = "idle" | "loading" | "success" | "invalid-token" | "unauthorized";

type GoogleCallbackResponse = {
  profile: {
    email: string;
    name: string;
  };
  session: {
    access_token: string;
  };
};

export function GoogleCallbackForm() {
  const [idToken, setIdToken] = useState("demo_google_id_token");
  const [state, setState] = useState<CallbackState>("idle");
  const [profileName, setProfileName] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");

    try {
      const response = await apiPost<GoogleCallbackResponse>("/auth/google/callback", {
        id_token: idToken
      });
      storeAccessToken(response.session.access_token);
      setProfileName(response.profile.name);
      setState("success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "";
      setState(message.includes("401") ? "invalid-token" : "unauthorized");
    }
  }

  return (
    <section className="panel stack">
      <form className="form-grid" onSubmit={submit}>
        <label htmlFor="google-id-token">Google ID token</label>
        <textarea
          id="google-id-token"
          name="google-id-token"
          onChange={(event) => setIdToken(event.target.value)}
          required
          value={idToken}
        />
        <div className="actions">
          <button className="button" disabled={state === "loading"} type="submit">
            {state === "loading" ? "Signing in..." : "Complete sign-in"}
          </button>
        </div>
      </form>

      {state === "success" && (
        <p className="status">Signed in as {profileName}. Tenant session stored.</p>
      )}
      {state === "invalid-token" && (
        <p className="muted">Google rejected this token. Start the sign-in flow again.</p>
      )}
      {state === "unauthorized" && (
        <p className="muted">
          This Google account does not have an active platform membership.
        </p>
      )}
    </section>
  );
}
