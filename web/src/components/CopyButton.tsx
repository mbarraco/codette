import { useState } from "react";
import { copyToClipboard } from "../utils/clipboard";
import styles from "./CopyButton.module.css";

type CopyButtonProps = {
  text: string;
};

function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await copyToClipboard(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  };

  return (
    <>
      <button type="button" className={styles.copyButton} onClick={handleCopy}>
        Copy
      </button>
      {copied ? <span className={styles.copiedTag}>Copied</span> : null}
    </>
  );
}

export default CopyButton;
