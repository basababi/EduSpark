import clsx from "clsx";
import { PropsWithChildren } from "react";

type ButtonProps = {
  variant?: "primary" | "secondary" | "ghost";
  href?: string;
  onClick?: () => void;
};

export const Button = ({ variant = "primary", children, href, onClick }: PropsWithChildren<ButtonProps>) => {
  const base =
    "inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-colors duration-150";
  const styles = {
    primary: "bg-primary text-white hover:bg-primary/90 shadow-soft",
    secondary: "bg-white text-primary border border-primary hover:bg-primary/5",
    ghost: "bg-transparent text-primary hover:bg-primary/10",
  };
  const className = clsx(base, styles[variant]);
  if (href) {
    return (
      <a className={className} href={href}>
        {children}
      </a>
    );
  }
  return (
    <button className={className} onClick={onClick}>
      {children}
    </button>
  );
};
