class Fern < Formula
  desc "Voice training feedback companion that integrates with dictation workflows"
  homepage "https://github.com/autumnsgrove/fern"
  url "https://github.com/autumnsgrove/fern/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"

  depends_on "python@3.11"
  depends_on "uv" => :recommended

  def install
    # Copy the entire project
    cp_r "../fern", buildpath

    # Install Python dependencies and the CLI
    system "uv", "sync"
    system "uv", "pip", "install", "-e", "."

    # Install Hammerspoon configuration
    (pkgshare/"hammerspoon").install "hammerspoon/init.lua"
    (pkgshare/"hammerspoon").install "hammerspoon/overlay.lua"
    (pkgshare/"hammerspoon").install "hammerspoon/charts.lua"
    (pkgshare/"hammerspoon").install "hammerspoon/chart_view.lua"

    # Create symlinks for CLI
    bin.install_symlink "fern"
  end

  def post_install
    # Create data directory
    (HOMEBREW_PREFIX/".fern").mkdir
    (HOMEBREW_PREFIX/".fern/clips").mkdir
    (HOMEBREW_PREFIX/".fern/archive").mkdir

    puts ""
    puts "🌿 Fern installed successfully!"
    puts ""
    puts "To set up Hammerspoon:"
    puts "  mkdir -p ~/.hammerspoon"
    puts "  ln -sf #{pkgshare}/hammerspoon/init.lua ~/.hammerspoon/fern.lua"
    puts "  echo 'require(\"fern\")' >> ~/.hammerspoon/init.lua"
    puts ""
    puts "Then reload Hammerspoon (Ctrl+Cmd+R)"
  end

  test do
    # Basic CLI test
    assert_match "Fern", shell_output("#{bin}/fern --help")
  end
end
