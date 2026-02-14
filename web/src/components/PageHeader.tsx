import type { ReactNode } from "react";
import styles from "./PageHeader.module.css";

type PageHeaderProps = {
  title: string;
  action?: ReactNode;
};

function PageHeader({ title, action }: PageHeaderProps) {
  return (
    <div className={styles.header}>
      <h1>{title}</h1>
      {action}
    </div>
  );
}

export default PageHeader;
