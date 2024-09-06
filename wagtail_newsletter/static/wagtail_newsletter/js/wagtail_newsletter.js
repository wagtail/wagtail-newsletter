window.wagtail.app.register("wn-panel",
  class extends window.StimulusModule.Controller {
    static targets = [
      "sendButton",
      "scheduleButton",
    ]

    static values = {
      recipientsUrl: String
    }

    get sendButtonProgress() {
      return this.application.getControllerForElementAndIdentifier(
        this.sendButtonTarget, "w-progress"
      );
    }

    get scheduleButtonProgress() {
      return this.application.getControllerForElementAndIdentifier(
        this.scheduleButtonTarget, "w-progress"
      );
    }

    get recipientsRequiredDialog() {
      return this.application.getControllerForElementAndIdentifier(
        document.querySelector("#wn-recipients-required"), "w-dialog"
      );
    }

    /*
     * Get the currently selected `newsletter_recipients` ID. If no recipients
     * are selected, show a dialog with an error message.
     */
    getRecipients() {
      const form = this.element.closest("form");
      const recipientsId = form.querySelector("[name=newsletter_recipients]").value;
      if (!recipientsId) {
        this.recipientsRequiredDialog.show();
        return;
      }
      return recipientsId;
    }

    async getRecipientsData(recipientsId) {
      try {
        const url = new URL(this.recipientsUrlValue, window.location.href);
        url.searchParams.set("pk", recipientsId);
        const response = await fetch(url);
        if (response.status < 200 || response.status >= 300) {
          throw new Error(`Response status is ${response.status} ${response.statusText}`);
        }
        return await response.json();
      }
      catch (error) {
        console.error(error);
        alert("Error fetching recipients");
      }
    }

    /*
     * Work-around for https://github.com/wagtail/wagtail/issues/12057
     */
    deactivateProgress(progress) {
      progress.loadingValue = false;
    }

    async sendCampaign() {
      const recipientsId = this.getRecipients();
      if (!recipientsId) {
        return;
      }

      this.sendButtonProgress.activate();
      const detail = await this.getRecipientsData(recipientsId);
      if (detail) {
        this.dispatch("showSendDialog", { detail });
      }

      this.deactivateProgress(this.sendButtonProgress);
    }

    async scheduleCampaign() {
      const recipientsId = this.getRecipients();
      if (!recipientsId) {
        return;
      }

      this.scheduleButtonProgress.activate();
      const detail = await this.getRecipientsData(recipientsId);
      if (detail) {
        this.dispatch("showScheduleDialog", { detail });
      }

      this.deactivateProgress(this.scheduleButtonProgress);
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

      /* In the case of the "Unschedule" button, if the user has unsaved
       * changes, and is presented with the browser dialog asking "Are you sure
       * you want to leave this page?", and they cancel the action, the
       * "Unschedule" button will be stuck with a spinner until the
       * ProgressController times out. Better to cancel the dialog because
       * we've already warned the user that they will lose any unsaved changes.
       */
      window.addEventListener(
        'w-unsaved:confirm',
        (event) => {
          event.preventDefault();
        },
        { once: true },
      );
    }
  }
);
