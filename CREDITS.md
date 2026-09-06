# Remembering the Beginning

pygwin did not start from nothing. It started from [xonsh](https://github.com/xonsh/xonsh),
a full featured, cross platform, Python powered shell built and maintained by the
xonsh developers and its community of contributors since 2015. pygwin's parser, execer,
built-in shells, completion system, and the large majority of the code in the `xonsh/`
directory of this repository are that project's work, copied into this repo and given a
new name, a new license, and a new direction.

Nothing in this file is meant to erase that. It is meant to keep it visible.

## The original license

The xonsh code this project is built on was distributed under the following license.
It is reproduced here in full, unmodified, exactly as it appeared in the upstream project,
because keeping it visible is a condition of using that code at all, not just a courtesy.

```
Copyright 2015-2016, the xonsh developers. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE XONSH DEVELOPERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE XONSH DEVELOPERS OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of the stakeholders of the xonsh project or the employers of xonsh developers.
```

BSD 2-Clause code is compatible with the GNU General Public License, and permits
relicensing a combined or derivative work under the GPL, which is what this repository
does: see [LICENSE](LICENSE). That permission does not erase the original notice above,
which is why it lives here, in full, rather than being summarized away.

The full list of everyone who has contributed to xonsh over the years is kept in
that project's own repository, not copied here, because it changes independently of
this fork and belongs to them, not to pygwin. See
[github.com/xonsh/xonsh](https://github.com/xonsh/xonsh) and its `.authors.yml` and
`.mailmap` for the current record.

## Where pygwin diverges

pygwin is a rebrand and, over time, a slimmed-down build of xonsh, not a drop-in
replacement maintained in lockstep with it. Where the two diverge, that divergence is
pygwin's responsibility, not xonsh's. See [ROADMAP.md](ROADMAP.md) for what has changed
so far and what is planned.

## Credit

- **xonsh** and its developers: the shell engine, parser, and the large majority of the
  code in this repository. Thank you for building something worth forking.
- **Dominick** (dommcpro@gmail.com): pygwin's rebrand, its performance and observability
  direction, and the changes layered on top of xonsh from here forward.
