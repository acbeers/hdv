# Homebrew formula for HDV (Hierarchical Data Viewer)
# To use: brew install path/to/Formula/hdv.rb
# Or add this tap and brew install youruser/hdv/hdv
class Hdv < Formula
  desc "Hierarchical Data Viewer - interactive CSV drill-down for the terminal"
  homepage "https://github.com/yourusername/hdv"
  url "https://files.pythonhosted.org/packages/.../hdv-0.1.0.tar.gz"
  sha256 "..."

  depends_on "python@3.10"

  def install
    venv = virtualenv_create(libexec, "python3.10")
    venv.pip_install buildpath
    bin.install_symlink libexec/"bin/hdv"
  end

  test do
    assert_match "usage", shell_output("#{bin}/hdv --help")
  end
end
