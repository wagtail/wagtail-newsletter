window.wagtail.app.register("wn-panel",
  class extends window.StimulusModule.Controller {
    static targets = [
      "sendButton",
    ]

    static values = {
      recipientsUrl: String
    }

    get sendButtonProgress() {
      return this.application.getControllerForElementAndIdentifier(
        this.sendButtonTarget, "w-progress"
      );
    }

    get sendRecipientsRequiredDialog() {
      return this.application.getControllerForElementAndIdentifier(
        document.querySelector("#wn-recipients-required"), "w-dialog"
      );
    }

    async sendCampaign() {
      const form = this.element.closest("form");
      const recipientsId = form.querySelector("[name=newsletter_recipients]").value;
      if (!recipientsId) {
        this.sendRecipientsRequiredDialog.show();
        return;
      }

      this.sendButtonProgress.activate();
      const url = new URL(this.recipientsUrlValue, window.location.href);
      url.searchParams.set("pk", recipientsId);

      try {
        const response = await fetch(url);
        if (response.status < 200 || response.status >= 300) {
          throw new Error(`Response status is ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        this.dispatch("showSendDialog", { detail: data });
      }
      catch (error) {
        console.error(error);
        alert("Error fetching recipients");
      }
      finally {
        // https://github.com/wagtail/wagtail/issues/12057
        this.sendButtonProgress.loadingValue = false;
      }
    }
  }
);


window.wagtail.app.register("wn-send",
  class extends window.StimulusModule.Controller {
    static targets = [
      "message",
    ];

    get dialog() {
      return this.application.getControllerForElementAndIdentifier(
        this.element.closest("[data-controller=w-dialog]"), "w-dialog"
      );
    }

    show(event) {
      const { name, member_count } = event.detail;
      this.messageTarget.textContent = `Sending campaign to ${name}, with ${member_count} recipients.`;
      this.dialog.show();
    }
  }
);


window.wagtail.app.register("wn-submit",
  class extends window.StimulusModule.Controller {
    static targets = [
      "button",
    ]

    get button() {
      return this.hasButtonTarget ? this.buttonTarget : this.element;
    }

    /* Capture the keydown.enter event from the input element and convert it
     * into a click event on the correct button.
     */
    submit(event) {
      // Stimulus has trouble with autofill
      // (https://github.com/hotwired/stimulus/issues/743), so better
      // double-check the event type ourselves.
      if (event.key !== "Enter") return;

      this.button.click();
    }

    /* Dispatch an event to announce that a particular button was clicked. This
     * is caught by the buttons in the panel so that they can trigger their
     * `w-progress` spinners.
     *
     * The event name is picked up from the button's value attribute. So for a
     * button defined like this:
     *
     * <button
     *    type="submit"
     *    name="newsletter-action"
     *    value="send_test_email"
     * >Send test email</button>
     *
     * the component will dispatch an event named `wn-submit:send_test_email`.
     *
     * This helps each user-visible non-submit button to catch the right event
     * and trigger its spinner.
     */
    sendEvent(event) {
      const eventName = this.button.value;
      this.dispatch(eventName, { detail: { event } });
    }
  }
);
