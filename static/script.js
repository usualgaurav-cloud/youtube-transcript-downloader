const button = document.querySelector("#download");

button.addEventListener("click", async () => {
    const urls = document.querySelector("#urls").value;

    const response = await fetch("/download", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ urls: urls })
    });

    if (!response.ok) {
        const data = await response.json();
        alert(data.error);
        return;
    }

    const blob = await response.blob();

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "transcripts.zip";
    link.click();
});