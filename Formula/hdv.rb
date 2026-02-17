# Homebrew formula for HDV (Hierarchical Data Viewer)
# To use: brew install path/to/Formula/hdv.rb
# Or add this tap and brew install youruser/hdv/hdv
class Hdv < Formula
  desc "Hierarchical Data Viewer - interactive CSV drill-down for the terminal"
  homepage "https://github.com/acbeers/hdv"
  url "https://github.com/acbeers/hdv/releases/download/v0.1.0/hdv-0.1.0.tar.gz"
  sha256 "83aa70030f6fb07451922296335963d85e9b3d8643df13edb9c2ff383dc0b1c9"

  depends_on "python@3.13"

  def install
    venv = virtualenv_create(libexec, "python3.13")
    venv.pip_install buildpath
    bin.install_symlink libexec/"bin/hdv"
    man1.install "share/man/man1/hdv.1"
  end

  test do
    assert_match "usage", shell_output("#{bin}/hdv --help")
  end
end
