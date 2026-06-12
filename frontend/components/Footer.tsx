import { FileText } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border-default/40 bg-[#0A0E1A] px-6 py-12">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded border border-brand" />
              <span className="text-lg font-semibold text-text-primary">
                Lumint
              </span>
            </div>
            <p className="mt-2 max-w-md text-sm text-text-secondary">
              Multimodal fraud intelligence for India&apos;s digital payment
              ecosystem.
            </p>
          </div>

          {/* Project Links */}
          <div>
            <h4 className="text-sm font-semibold text-text-primary">Project</h4>
            <ul className="mt-3 space-y-2 text-sm text-text-secondary">
              <li>
                <a
                  href="https://github.com/tanmay-alpha/Lumint"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-text-primary transition-colors"
                >
                  GitHub
                </a>
              </li>
              <li>
                <Link
                  href="/dashboard/research"
                  className="hover:text-text-primary transition-colors"
                >
                  Research Paper
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard"
                  className="hover:text-text-primary transition-colors"
                >
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 className="text-sm font-semibold text-text-primary">Connect</h4>
            <ul className="mt-3 space-y-2 text-sm text-text-secondary">
              <li>
                <a
                  href="https://github.com/tanmay-alpha/Lumint"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-text-primary transition-colors"
                >
                  ⭐ Star on GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://www.linkedin.com/in/tanmaymangal/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-text-primary transition-colors"
                >
                  💼 LinkedIn
                </a>
              </li>
              <li>
                <a
                  href="https://huggingface.co/tanmay-alpha"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 hover:text-text-primary transition-colors"
                >
                  <FileText className="h-4 w-4" />
                  HuggingFace
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom row */}
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border-default/40 pt-8 md:flex-row">
          <p className="text-xs text-text-muted">
            © 2026 Lumint · MIT License
          </p>
          <p className="text-xs text-text-muted">
            Built by{" "}
            <a
              href="https://www.linkedin.com/in/tanmaymangal/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand hover:underline"
            >
              Tanmay
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
