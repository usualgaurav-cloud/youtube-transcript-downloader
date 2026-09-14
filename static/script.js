const button = document.querySelector("#download");
const urlsInput = document.querySelector("#urls");

button.addEventListener("click", async () => {
    const urls = urlsInput.value.trim();

    if (!urls) {
        alert("Please enter at least one YouTube URL.");
        return;
    }

    button.disabled = true;
    button.innerHTML = "Processing your videos...";

    const oldResults = document.querySelector("#results");

    if (oldResults) {
        oldResults.remove();
    }

    try {
        const response = await fetch("/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ urls })
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Something went wrong.");
            return;
        }

        button.innerHTML = "Preparing your PDFs...";

        const resultsSection = document.createElement("section");
        resultsSection.id = "results";
        resultsSection.className = "results-section";

        const heading = document.createElement("h2");
        heading.textContent =
            `${data.results.length} PDF${data.results.length === 1 ? "" : "s"} ready`;

        resultsSection.appendChild(heading);

        data.results.forEach((result, index) => {
            const resultCard = document.createElement("div");
            resultCard.className = "result-card";

            const info = document.createElement("div");
            info.className = "result-info";

            const number = document.createElement("span");
            number.className = "result-number";
            number.textContent = `PDF ${index + 1}`;

            const title = document.createElement("p");
            title.className = "result-title";
            title.textContent = result.title;

            info.appendChild(number);
            info.appendChild(title);

            const downloadButton = document.createElement("button");
            downloadButton.className = "result-download";
            downloadButton.textContent = "Download PDF";

            downloadButton.addEventListener("click", () => {
                window.location.href = `/pdf/${result.pdf_id}`;
            });

            resultCard.appendChild(info);
            resultCard.appendChild(downloadButton);

            resultsSection.appendChild(resultCard);
        });

        if (data.failures.length > 0) {
            const failuresHeading = document.createElement("h3");
            failuresHeading.textContent = "Could not create";

            resultsSection.appendChild(failuresHeading);

            data.failures.forEach((failure) => {
                const failureText = document.createElement("p");

                failureText.textContent =
                    `${failure.url} — ${failure.reason}`;

                resultsSection.appendChild(failureText);
            });
        }

        document.querySelector("main").appendChild(resultsSection);

    } catch (error) {
        console.error(error);
        alert("Something went wrong while processing the videos.");

    } finally {
        button.disabled = false;
        button.innerHTML = 'Get PDFs <span>→</span>';
    }
});