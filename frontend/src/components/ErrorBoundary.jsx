import { Component } from "react";

// Phase 15 -- last line of defence. If any page throws while
// rendering (for example a stored result with an unexpected shape),
// React would otherwise unmount the whole app and leave a white
// screen in the middle of a presentation. This shows a calm message
// with a way back instead. It resets when the route changes.
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null, resetKey: props.resetKey };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  static getDerivedStateFromProps(props, state) {
    // Navigating to another page clears a previous crash.
    if (props.resetKey !== state.resetKey) return { error: null, resetKey: props.resetKey };
    return null;
  }

  componentDidCatch(error) {
    console.error("Page crashed while rendering:", error);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="text-base font-semibold text-red-800">This page could not be displayed.</p>
        <p className="mt-2 text-sm text-red-700">
          Nothing was changed. Go to another page, or reload and pick a stored experiment from Experiment History.
        </p>
        <details className="mt-3">
          <summary className="cursor-pointer text-xs font-medium text-red-700">Technical details</summary>
          <p className="mt-1 break-words font-mono text-xs text-red-800">{String(this.state.error?.message || this.state.error)}</p>
        </details>
        <button
          type="button"
          onClick={() => window.location.assign("/history")}
          className="mt-4 rounded-md bg-red-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-800"
        >
          Open Experiment History
        </button>
      </div>
    );
  }
}
