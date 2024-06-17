window.wagtail.app.register("wn-panel",
  class extends window.StimulusModule.Controller {
    static targets = [
      "testButton",
      "testAddress",
      "testSubmit",
    ]

    get testButtonProgress() {
      return this.application.getControllerForElementAndIdentifier(
        this.testButtonTarget, "w-progress"
      );
    }

    test(event) {
      this.testAddressTarget.value = event.detail.address;
      this.testButtonProgress.activate();
      this.testSubmitTarget.click();
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
