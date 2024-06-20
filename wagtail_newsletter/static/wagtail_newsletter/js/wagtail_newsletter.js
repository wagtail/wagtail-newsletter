window.wagtail.app.register("wn-panel",
  class extends window.StimulusModule.Controller {
    static targets = [
      "testButton",
      "testAddress",
      "testSubmit",
      "sendButton",
      "sendSubmit",
    ]

    static values = {
      recipientsUrl: String
    }

    get testButtonProgress() {
      return this.application.getControllerForElementAndIdentifier(
        this.testButtonTarget, "w-progress"
      );
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

    test(event) {
      this.testAddressTarget.value = event.detail.address;
      this.testButtonProgress.activate();
      this.testSubmitTarget.click();
    }

    async clickSend() {
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

    send() {
      this.sendButtonProgress.activate();
      this.sendSubmitTarget.click();
    }
  }
);


window.wagtail.app.register("wn-test",
  class extends window.StimulusModule.Controller {
    get dialog() {
      return this.application.getControllerForElementAndIdentifier(
        this.element.closest("[data-controller=w-dialog]"), "w-dialog"
      );
    }

    submit() {
      const address = this.element.querySelector("input[name=email]").value;
      this.dispatch("submit", { detail: { address } });
      this.dialog.hide();
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

    submit() {
      this.dispatch("submit");
      this.dialog.hide();
    }
  }
);
