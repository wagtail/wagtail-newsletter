window.wagtail.app.register("wn-panel",
  class extends window.StimulusModule.Controller {
    static targets = [
      "testButton",
      "testAddress",
      "testSubmit",
    ]

    get testButton() {
      return this.application.getControllerForElementAndIdentifier(
        this.testButtonTarget, "w-progress"
      );
    }

    test(event) {
      this.testAddressTarget.value = event.detail.address;
      this.testButton.activate();
      this.testSubmitTarget.click();
    }
  }
);


window.wagtail.app.register("wn-test",
  class extends window.StimulusModule.Controller {
    static targets = [
      "address",
    ]

    get dialog() {
      return this.application.getControllerForElementAndIdentifier(
        this.element.closest("[data-controller=w-dialog]"), "w-dialog"
      );
    }

    send() {
      this.dispatch("send", { detail: { address: this.addressTarget.value } });
      this.dialog.hide();
    }
  }
);
